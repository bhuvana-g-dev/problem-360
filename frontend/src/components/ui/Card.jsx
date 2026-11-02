export default function Card({ className = '', children, ...rest }) {
  return <div className={`rounded-card bg-white p-5 shadow-card ${className}`} {...rest}>{children}</div>
}
