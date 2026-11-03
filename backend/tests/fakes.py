"""TEST DOUBLES. These exist only in tests. They prove the wiring, permissions and orchestration;
they do NOT prove that Amazon Bedrock or the hosted Strands Decider behave correctly.
The Strands Agent loop itself is the real strands-agents SDK; only the language model and the Decider endpoint are replaced."""
import json
from datetime import datetime, timezone

from strands.models import Model


class InMemoryStorage:
    def __init__(self): self.files = {}
    def put(self, path, data, content_type): self.files[path] = (data, content_type)
    def exists(self, path): return path in self.files
    def signed_url(self, path, minutes=60): return f"https://signed.test/{path}"


class InMemoryDecisionRepo:
    def __init__(self): self.docs, self.audits, self.incidents = {}, {}, {}
    def save(self, pid, doc): self.docs[pid] = doc
    def get(self, pid): return self.docs.get(pid)
    def audit(self, pid, t, detail=None): self.audits.setdefault(pid, []).append({"type": t, "detail": detail or {}, "at": datetime.now(timezone.utc)})
    def list_audit(self, pid): return self.audits.get(pid, [])
    def create_incident(self, ref, doc): self.incidents[ref] = doc
    def get_incident(self, ref): return self.incidents.get(ref)


class InMemoryPostRepo:
    def __init__(self): self.posts, self.likes, self.comments, self.notes = {}, {}, {}, []
    def create(self, pid, data):
        self.posts[pid] = {**data, "id": pid, "createdAt": datetime.now(timezone.utc), "updatedAt": datetime.now(timezone.utc)}
    def get(self, pid): return dict(self.posts[pid]) if pid in self.posts else None
    def list(self, locality=None, category=None, author_uid=None, limit=200):
        rows = [p for p in self.posts.values() if (not locality or p["locality"] == locality) and (not category or p["category"] == category)
                and (not author_uid or p["authorUid"] == author_uid)]
        return sorted(rows, key=lambda p: p["createdAt"], reverse=True)[:limit]
    def recent_for_duplicates(self, locality, since, exclude_id):
        return [p for p in self.posts.values() if p["locality"] == locality and p["id"] != exclude_id and p["createdAt"] >= since]
    def set_decision(self, pid, state, summary): self.posts[pid].update(decisionState=state, decision=summary)
    def list_community_opportunities(self, limit=100):
        return sorted([dict(p) for p in self.posts.values() if (p.get("decision") or {}).get("action") == "SUGGEST_COMMUNITY_ACTION"], key=lambda p: p["createdAt"], reverse=True)
    def toggle_like(self, pid, uid):
        if pid not in self.posts: return None
        s = self.likes.setdefault(pid, set())
        s.symmetric_difference_update({uid}); self.posts[pid]["likeCount"] = len(s)
        return {"likedByMe": uid in s, "likeCount": len(s)}
    def liked_ids(self, ids, uid): return {i for i in ids if uid in self.likes.get(i, set())}
    def list_comments(self, pid, limit=200): return self.comments.get(pid, [])
    def add_comment(self, pid, cid, data):
        self.comments.setdefault(pid, []).append({**data, "id": cid, "createdAt": datetime.now(timezone.utc)}); self.posts[pid]["commentCount"] += 1
    def add_notification(self, uid, text, pid): self.notes.append({"id": str(len(self.notes)), "uid": uid, "text": text, "postId": pid, "createdAt": datetime.now(timezone.utc)})
    def list_notifications(self, uid, limit=50): return [n for n in reversed(self.notes) if n["uid"] == uid]   # newest first, like the real repo


class FakeDecider:
    """Keyword heuristics standing in for the hosted Decider endpoint (same request/response shape as DeciderClient)."""
    calls = 0
    def decide(self, state, questions):
        FakeDecider.calls += 1
        t = state.lower()
        danger = any(w in t for w in ("wire", "manhole", "fire", "trapped", "collapsed", "gas"))
        dept = ("electricity" if "wire" in t or "power" in t else "roads" if "pothole" in t else "sanitation" if "garbage" in t or "litter" in t
                else "street_lighting" if "street light" in t else "unclear")
        return {"urgent": {"noul": 0.95 if danger else 0.05}, "department": {"choice": dept, "confidence": 0.9 if dept != "unclear" else 0.2},
                "community": {"noul": 0.9 if any(w in t for w in ("litter", "weeds", "leaves")) else 0.1},
                "vague": {"noul": 0.95 if len(t.split("report:")[-1].strip()) < 25 else 0.05}}


class ScriptedModel(Model):
    """Deterministic stand-in for the LLM that drives the REAL Strands event loop and graph. As the planner it calls every tool,
    reads the real tool results, then submits AgentChoice through Strands' own structured-output tool. As the critic (no domain
    tools) it submits a Critique: ok unless `critic_ok=False`. `planner_runs` counts planner runs, so tests can prove the hook stopped them."""
    planner_runs = 0

    def __init__(self, force_action=None, critic_ok=True):
        self.force, self.critic_ok, self.config = force_action, critic_ok, {}
    def update_config(self, **kw): self.config.update(kw)
    def get_config(self): return self.config
    async def structured_output(self, output_model, prompt, system_prompt=None, **kw):
        raise NotImplementedError
        yield

    @staticmethod
    def _results(messages):
        names, out = {}, {}
        for m in messages:
            for b in m["content"]:
                if "toolUse" in b: names[b["toolUse"]["toolUseId"]] = b["toolUse"]["name"]
                if "toolResult" in b:
                    c = b["toolResult"]["content"][0]
                    try:
                        out[names.get(b["toolResult"]["toolUseId"], "?")] = c["json"] if "json" in c else json.loads(c["text"])
                    except ValueError:  # Strands hands tool exceptions to the model as an error text
                        out[names.get(b["toolResult"]["toolUseId"], "?")] = {"error": c.get("text", "")}
        return out

    @staticmethod
    def _events(calls=None, text=None):
        yield {"messageStart": {"role": "assistant"}}
        if text:
            yield {"contentBlockStart": {"start": {}}}; yield {"contentBlockDelta": {"delta": {"text": text}}}; yield {"contentBlockStop": {}}
        for i, (name, inp) in enumerate(calls or []):
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": f"t{i}-{name}", "name": name}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(inp)}}}}
            yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "tool_use" if calls else "end_turn"}}
        yield {"metadata": {"usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2}, "metrics": {"latencyMs": 1}}}

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        domain = ["search_nearby_reports", "detect_duplicates", "assess_urgency", "recommend_department", "recommend_community_action"]
        res = self._results(messages)
        names = [t["name"] for t in tool_specs or []]
        if not set(names) & set(domain):  # critic node
            if res:
                for e in self._events(text="done"): yield e
                return
            verdict = {"ok": True, "problems": []} if self.critic_ok else {"ok": False, "problems": ["summary: scripted critic rejects it"]}
            for e in self._events([(names[0], verdict)]): yield e
            return
        if "assess_urgency" not in res:
            ScriptedModel.planner_runs += 1
            for e in self._events([(n, {}) for n in domain]): yield e
            return
        out_tool = next((t["name"] for t in tool_specs if t["name"] not in domain), None)
        if out_tool and out_tool not in res and "AgentChoice" not in res:
            if "error" in res["assess_urgency"]: action = "ESCALATE_FOR_HUMAN_REVIEW"   # a model that gives up after a tool error
            elif self.force: action = self.force
            elif res["assess_urgency"]["urgent"]: action = "FLAG_URGENT"
            elif res["detect_duplicates"]["isLikelyDuplicate"]: action = "CHECK_DUPLICATE"
            elif res["recommend_community_action"]["suitable"]: action = "SUGGEST_COMMUNITY_ACTION"
            elif res["recommend_department"]["confident"]: action = "ROUTE_TO_DEPARTMENT"
            else: action = "ESCALATE_FOR_HUMAN_REVIEW"
            payload = {"action": action, "summary": f"Scripted test summary for {action}.", "reasoning": "Scripted test model following tool results.", "questions": ["What is wrong and where exactly?"]}
            for e in self._events([(out_tool, payload)]): yield e
            return
        for e in self._events(text="done"): yield e


# ------------------------- Phase 5 in-memory doubles -------------------------
from app.repositories.accounts import AccountExists  # noqa: E402


class MemCommunity:
    """Same interface as CommunityRepository, including capacity/past/cancelled rules."""
    def __init__(self): self.groups, self.gm, self.events, self.regs, self.updates = {}, {}, {}, {}, {}
    @staticmethod
    def _now(): return datetime.now(timezone.utc)
    def create_group(self, gid, d): self.groups[gid] = {**d, "id": gid, "memberCount": 0, "createdAt": self._now()}
    def get_group(self, gid): return dict(self.groups[gid]) if gid in self.groups else None
    def list_groups(self, org_id=None, locality=None, limit=200):
        return sorted([g for g in self.groups.values() if (not org_id or g["orgId"] == org_id) and (not locality or g["locality"] == locality)], key=lambda g: g["createdAt"], reverse=True)
    def join_group(self, gid, uid, name):
        if gid not in self.groups: return "missing"
        s = self.gm.setdefault(gid, {})
        if uid in s: return "already"
        s[uid] = name; self.groups[gid]["memberCount"] = len(s); return "ok"
    def leave_group(self, gid, uid):
        s = self.gm.get(gid, {})
        if uid not in s: return False
        del s[uid]; self.groups[gid]["memberCount"] = len(s); return True
    def joined_group_ids(self, gids, uid): return {g for g in gids if uid in self.gm.get(g, {})}
    def list_group_members(self, gid): return [{"uid": u, "name": n} for u, n in self.gm.get(gid, {}).items()]
    def create_event(self, eid, d): self.events[eid] = {**d, "id": eid, "registrationCount": 0, "status": "scheduled", "createdAt": self._now()}
    def get_event(self, eid): return dict(self.events[eid]) if eid in self.events else None
    def list_events(self, org_id=None, locality=None, limit=200):
        return sorted([e for e in self.events.values() if (not org_id or e["orgId"] == org_id) and (not locality or e["locality"] == locality)], key=lambda e: e["startsAt"])
    def cancel_event(self, eid): self.events[eid]["status"] = "cancelled"
    def register(self, eid, uid, name):
        e = self.events.get(eid)
        if not e: return "missing"
        if e["status"] != "scheduled": return "cancelled"
        if e["startsAt"] < self._now(): return "past"
        r = self.regs.setdefault(eid, {})
        if uid in r: return "already"
        if e.get("capacity") is not None and e["registrationCount"] >= e["capacity"]: return "full"
        r[uid] = {"name": name, "registeredAt": self._now()}; e["registrationCount"] = len(r); return "ok"
    def unregister(self, eid, uid):
        r = self.regs.get(eid, {})
        if uid not in r: return False
        del r[uid]; self.events[eid]["registrationCount"] = len(r); return True
    def registered_event_ids(self, eids, uid): return {e for e in eids if uid in self.regs.get(e, {})}
    def list_registrations(self, eid): return [{"uid": u, **v} for u, v in self.regs.get(eid, {}).items()]
    def create_update(self, uid, d): self.updates[uid] = {**d, "id": uid, "createdAt": self._now()}
    def list_updates(self, org_id=None, limit=50):
        return sorted([u for u in self.updates.values() if not org_id or u["orgId"] == org_id], key=lambda u: u["createdAt"], reverse=True)[:limit]


class MemAccounts:
    """Same interface as AccountRepository (accounts, organizations, members, invites, verification)."""
    def __init__(self): self.users, self.orgs, self.members, self.invites, self.audit = {}, {}, {}, {}, []
    def get_user(self, uid): return self.users.get(uid)
    def get_organization(self, oid): return ({**self.orgs[oid], "id": oid} if oid in self.orgs else None)
    def get_membership(self, oid, uid): return self.members.get(f"{oid}_{uid}")
    def create_citizen(self, uid, email, name, loc):
        if uid in self.users: raise AccountExists()
        self.users[uid] = {"uid": uid, "email": email, "displayName": name, "accountType": "citizen", "locality": loc}
    def create_organization_with_owner(self, uid, email, contact, org):
        if uid in self.users: raise AccountExists()
        oid = f"org{len(self.orgs) + 1}"
        self.users[uid] = {"uid": uid, "email": email, "displayName": contact, "accountType": "organization", "locality": org["locality"], "organizationId": oid}
        self.orgs[oid] = {**org, "verificationStatus": "pending", "createdBy": uid, "createdAt": datetime.now(timezone.utc)}
        self.members[f"{oid}_{uid}"] = {"organizationId": oid, "uid": uid, "role": "owner", "displayName": contact, "email": email, "createdAt": datetime.now(timezone.utc)}
        return self.users[uid], oid
    def list_members(self, oid): return sorted([m for m in self.members.values() if m["organizationId"] == oid], key=lambda m: m["createdAt"])
    def set_member_role(self, oid, uid, role): self.members[f"{oid}_{uid}"]["role"] = role
    def remove_member(self, oid, uid): del self.members[f"{oid}_{uid}"]; self.users[uid]["organizationId"] = None
    def create_invite(self, code, d): self.invites[code] = {**d, "code": code, "status": "pending", "createdAt": datetime.now(timezone.utc)}
    def get_invite(self, code): return dict(self.invites[code]) if code in self.invites else None
    def list_invites(self, oid): return [i for i in self.invites.values() if i["organizationId"] == oid and i["status"] == "pending"]
    def revoke_invite(self, code): self.invites[code]["status"] = "revoked"
    def accept_invite(self, uid, email, contact, inv, locality):
        if uid in self.users: raise AccountExists()
        oid = inv["organizationId"]
        self.users[uid] = {"uid": uid, "email": email, "displayName": contact, "accountType": "organization", "locality": locality, "organizationId": oid}
        self.members[f"{oid}_{uid}"] = {"organizationId": oid, "uid": uid, "role": inv["role"], "displayName": contact, "email": email, "createdAt": datetime.now(timezone.utc)}
        self.invites[inv["code"]]["status"] = "accepted"
    def list_organizations(self, status=None): return [{**o, "id": i} for i, o in self.orgs.items() if not status or o["verificationStatus"] == status]
    def set_verification(self, oid, status, by, note):
        self.orgs[oid]["verificationStatus"] = status; self.audit.append({"org": oid, "status": status, "by": by, "note": note})
