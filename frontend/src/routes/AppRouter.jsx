import { Navigate, Route, Routes } from 'react-router-dom'
import { ConfigGate, PublicOnly, RequireAccount, RequireVerifiedOrg } from './guards.jsx'
import { ACCOUNT_TYPES } from '../config/constants.js'
import CitizenLayout from '../components/layout/CitizenLayout.jsx'
import OrganizationLayout from '../components/layout/OrganizationLayout.jsx'
import Landing from '../pages/public/Landing.jsx'
import NotFound from '../pages/public/NotFound.jsx'
import CitizenLogin from '../pages/citizen/CitizenLogin.jsx'
import CitizenRegister from '../pages/citizen/CitizenRegister.jsx'
import CitizenHome from '../pages/citizen/CitizenHome.jsx'
import Explore from '../pages/citizen/Explore.jsx'
import ReportNew from '../pages/citizen/ReportNew.jsx'
import PostResult from '../pages/citizen/PostResult.jsx'
import Community from '../pages/citizen/Community.jsx'
import Profile from '../pages/citizen/Profile.jsx'
import Notifications from '../pages/citizen/Notifications.jsx'
import OrgLogin from '../pages/organization/OrgLogin.jsx'
import OrgRegister from '../pages/organization/OrgRegister.jsx'
import OrgDashboard from '../pages/organization/OrgDashboard.jsx'
import OrgGroups from '../pages/organization/OrgGroups.jsx'
import OrgEvents from '../pages/organization/OrgEvents.jsx'
import OrgUpdates from '../pages/organization/OrgUpdates.jsx'
import OrgMembers from '../pages/organization/OrgMembers.jsx'
import OrgCivic from '../pages/organization/OrgCivic.jsx'
import OrgJoin from '../pages/organization/OrgJoin.jsx'
import OrgSettings from '../pages/organization/OrgSettings.jsx'
import ComingSoon from '../pages/shared/ComingSoon.jsx'

const soon = (title, phase) => <ComingSoon title={title} phase={phase} />

export default function AppRouter() {
  return (
    <ConfigGate>
      <Routes>
        <Route path="/" element={<Landing />} />

        {/* Separate auth flows per account type */}
        <Route element={<PublicOnly />}>
          <Route path="/citizen/login" element={<CitizenLogin />} />
          <Route path="/citizen/register" element={<CitizenRegister />} />
          <Route path="/org/login" element={<OrgLogin />} />
          <Route path="/org/register" element={<OrgRegister />} />
          <Route path="/org/join" element={<OrgJoin />} />
        </Route>

        {/* Citizen area — social feed layout */}
        <Route element={<RequireAccount type={ACCOUNT_TYPES.CITIZEN} />}>
          <Route path="/app" element={<CitizenLayout />}>
            <Route index element={<CitizenHome />} />
            <Route path="post/:id" element={<PostResult />} />
            <Route path="explore" element={<Explore />} />
            <Route path="report/new" element={<ReportNew />} />
            <Route path="my-reports" element={soon('My reports', 6)} />
            <Route path="groups" element={<Community />} />
            <Route path="notifications" element={<Notifications />} />
            <Route path="profile" element={<Profile />} />
          </Route>
        </Route>

        {/* Organization area — management workspace layout */}
        <Route element={<RequireAccount type={ACCOUNT_TYPES.ORGANIZATION} />}>
          <Route path="/org" element={<OrganizationLayout />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<OrgDashboard />} />
            <Route path="settings" element={<OrgSettings />} />
            <Route element={<RequireVerifiedOrg />}>
              <Route path="civic" element={<OrgCivic />} />
              <Route path="groups" element={<OrgGroups />} />
              <Route path="events" element={<OrgEvents />} />
              <Route path="updates" element={<OrgUpdates />} />
              <Route path="members" element={<OrgMembers />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </ConfigGate>
  )
}
