export interface ExplorerItemProps {
    level: number;
    type: 'file' | 'directory';
    isDir: boolean;
    isDragging?: boolean;
    isOver?: boolean;
    isOverlay?: boolean;
    isOpen?: boolean;
    transform?: string;
    transition?: string;
}