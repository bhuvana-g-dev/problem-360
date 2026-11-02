export const BRAND = { name: 'Problem 360', tagline: 'From Problems to Progress' }

export const ACCOUNT_TYPES = { CITIZEN: 'citizen', ORGANIZATION: 'organization', ADMIN: 'admin' }

// Route table: single source of truth for paths (see docs/ARCHITECTURE.md route map)
export const ROUTES = {
  home: '/',
  citizenLogin: '/citizen/login',
  citizenRegister: '/citizen/register',
  orgLogin: '/org/login',
  orgRegister: '/org/register',
  citizenHome: '/app',
  orgHome: '/org/dashboard',
}

export const homeFor = (type) =>
  type === ACCOUNT_TYPES.ORGANIZATION ? ROUTES.orgHome : type === ACCOUNT_TYPES.CITIZEN ? ROUTES.citizenHome : ROUTES.home

export const loginFor = (type) => (type === ACCOUNT_TYPES.ORGANIZATION ? ROUTES.orgLogin : ROUTES.citizenLogin)

export const VERIFICATION = { PENDING: 'pending', VERIFIED: 'verified', REJECTED: 'rejected' }

// Issue lifecycle (master prompt section 4). "Reopened" is a re-entry state, not a step.
export const ISSUE_STATUSES = ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Verified']

export const ORG_CATEGORIES = [
  'NGO / Non-profit', "Residents' welfare association", 'Student club / NSS / NCC',
  'Volunteer group', 'Trust / Foundation', 'Community / religious group', 'Other',
]

// Areas of Madurai city for the locality selector (editable list; not a municipal ward register).
export const MADURAI_LOCALITIES = [
  'Anna Nagar', 'Arapalayam', 'Avaniyapuram', 'Goripalayam', 'K. Pudur', 'KK Nagar', 'Melur Road',
  'Mattuthavani', 'Pasumalai', 'Sellur', 'Simmakkal', 'Subramaniapuram', 'Thallakulam', 'Thirunagar',
  'Thiruparankundram', 'Tirumangalam Road', 'Vilangudi', 'Villapuram', 'Vandiyur', 'Other (Madurai)',
]

export const ISSUE_CATEGORIES = [
  'Roads & potholes', 'Waste & sanitation', 'Water supply', 'Drainage & flooding', 'Street lighting',
  'Electricity', 'Public transport', 'Parks & public spaces', 'Public safety', 'Other',
]
