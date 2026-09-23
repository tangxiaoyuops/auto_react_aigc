import { useCallback, useRef } from 'react';
import { GripVertical } from 'lucide-react';

interface ResizerProps {
  onResize: (delta: number) => void;
  className?: string;
}

/**
 * 可拖拽的竖向分隔条（用于左右分栏调整宽度）
 * 拖拽过程中向 onResize 持续回调每帧的像素增量
 */
export default function Resizer({ onResize, className = '' }: ResizerProps) {
  const draggingRef = useRef(false);
  const startXRef = useRef(0);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      draggingRef.current = true;
      startXRef.current = e.clientX;
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';

      const handleMove = (ev: PointerEvent) => {
        if (!draggingRef.current) return;
        const dx = ev.clientX - startXRef.current;
        if (dx === 0) return;
        startXRef.current = ev.clientX;
        onResize(dx);
      };

      const stopDrag = () => {
        draggingRef.current = false;
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
        window.removeEventListener('pointermove', handleMove);
        window.removeEventListener('pointerup', stopDrag);
        window.removeEventListener('pointercancel', stopDrag);
      };

      window.addEventListener('pointermove', handleMove);
      window.addEventListener('pointerup', stopDrag);
      window.addEventListener('pointercancel', stopDrag);
    },
    [onResize]
  );

  return (
    <div
      onPointerDown={onPointerDown}
      role="separator"
      aria-orientation="vertical"
      title="拖拽调整宽度"
      className={`w-[6px] shrink-0 cursor-col-resize group flex items-center justify-center hover:bg-[#bcd8ff]/60 active:bg-[#bcd8ff] transition-colors select-none ${
        className
      }`}
    >
      <GripVertical size={12} className="text-[#b8bcc6] group-hover:text-[#0077ff] transition-colors" />
    </div>
  );
}