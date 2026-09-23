import { STATUS_LABEL, STATUS_COLOR, type Agent } from '../../types/agent';

interface Props {
  status: Agent['status'];
}

const STYLE: Record<string, string> = {
  default: 'bg-gray-100 text-gray-600',
  success: 'bg-green-100 text-green-600',
  warning: 'bg-orange-100 text-orange-600',
};

export default function AgentStatus({ status }: Props) {
  const color = STATUS_COLOR[status];
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${STYLE[color]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}