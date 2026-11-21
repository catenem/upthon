import React, { memo } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ModalType } from '../../routes';

// Importação dos ícones (SVGs)
import folderSvg from '../../assets/folder.svg';
import draglabeSvg from '../../assets/draglabe.svg';
import arrowSvg from '../../assets/arrow.svg';
import iconMp4Svg from '../../assets/file-mp4.svg';
import iconPdfSvg from '../../assets/file-pdf.svg';
import iconFileSvg from '../../assets/file-file.svg';
import iconImgSvg from '../../assets/file-img.svg';

import * as S from './style';

// Interface das propriedades do componente
interface FileItemProps {
    id: string;
    name: string;
    real_name: string;
    type: 'file' | 'directory';
    level: number;
    mp4_count?: number;
    pdf_count?: number;
    onClick?: (e: React.MouseEvent) => void;
    isOverlay?: boolean;
    isOpen?: boolean;
    onOpenModal: (type: ModalType, data?: any) => void;
    path?: string;
}

function FileItemComponent({
    id, 
    name, 
    real_name, 
    path, 
    type, 
    level,
    mp4_count = 0, 
    pdf_count = 0, 
    onClick,
    isOverlay = false, 
    isOpen = false,
    onOpenModal
}: FileItemProps) {
    
    // Hook de arrastar e soltar do @dnd-kit
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
        isOver
    } = useSortable({ id, disabled: isOverlay });

    const isDir = type === 'directory';
    const orderId = real_name?.match(/^\d+/)?.[0];

    // Seleção de ícones baseada no tipo e extensão do ficheiro
    const getFileIcon = () => {
        if (isDir) return folderSvg;
        
        const fileName = (real_name || name).toLowerCase();
        
        if (fileName.endsWith('.mp4') || fileName.endsWith('.ts') || fileName.endsWith('.mov')) {
            return iconMp4Svg;
        }

        if (fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || fileName.endsWith('.png')) {
            return iconImgSvg;
        }
        
        if (fileName.endsWith('.pdf')) {
            return iconPdfSvg;
        }

        return iconFileSvg;
    };

    // Trata o clique no botão de upload de forma isolada
    const handleUploadClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onOpenModal('uploader', {
            name: name,
            path: path
        });
    };

    return (
        <S.Container
            ref={setNodeRef}
            data-dnd-id={isOverlay ? undefined : id}
            level={level}
            isDragging={isDragging}
            isOver={isOver}
            isOverlay={isOverlay}
            isDir={isDir}
            transform={CSS.Translate.toString(transform)}
            transition={transition}
            {...attributes}
            {...listeners}
            onClick={onClick}
        >
            <S.IconBox level={level}>
                <img src={draglabeSvg} alt="drag" />

                {orderId && level > 0 && (
                    <S.OrderBadge>{orderId}</S.OrderBadge>
                )}

                <span className='box-folder'>
                    <img src={getFileIcon()} alt="file-icon" />
                </span>

                {isDir && (
                    <S.ArrowIcon isOpen={isOpen}>
                        <img className='arrowSvg' src={arrowSvg} alt="arrow" />
                    </S.ArrowIcon>
                )}
            </S.IconBox>

            <S.FileName isDir={isDir} level={level}>{name}</S.FileName>

            {isDir && level === 0 && (
                <S.boxContainer>
                    <span> {mp4_count || 0} videos</span>
                    <span> {pdf_count || 0} pdfs</span>
                    <button onClick={handleUploadClick}>
                        Fazer upload
                    </button>
                </S.boxContainer>
            )}
        </S.Container>
    );
}

// 💡 OTIMIZAÇÃO AVANÇADA:
// Função de comparação personalizada para o React.memo.
// Retorna 'true' se as props forem iguais (NÃO re-renderiza).
// Retorna 'false' se algo mudou (RE-RENDERIZA).
function arePropsEqual(prevProps: FileItemProps, nextProps: FileItemProps) {
    return (
        prevProps.id === nextProps.id &&
        prevProps.name === nextProps.name &&
        prevProps.real_name === nextProps.real_name &&
        prevProps.path === nextProps.path &&
        prevProps.type === nextProps.type &&
        prevProps.level === nextProps.level &&
        prevProps.isOpen === nextProps.isOpen &&
        prevProps.isOverlay === nextProps.isOverlay &&
        prevProps.mp4_count === nextProps.mp4_count &&
        prevProps.pdf_count === nextProps.pdf_count
        // Note que 'onOpenModal' e 'onClick' NÃO estão aqui.
        // Isto impede re-renders desnecessários quando o pai recria essas funções.
    );
}

export const FileItem = memo(FileItemComponent, arePropsEqual);