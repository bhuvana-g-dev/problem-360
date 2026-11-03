export default function Card({ as: Tag = 'div', className = '', children, ...rest }) {
  return <Tag className={`rounded-card bg-white p-5 shadow-card ${className}`} {...rest}>{children}</Tag>
}
