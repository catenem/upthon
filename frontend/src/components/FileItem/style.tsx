import styled, { css } from 'styled-components';

interface ContainerProps {
    level: number;
    isDragging?: boolean;
    isOver?: boolean;
    isOverlay?: boolean;
    isDir: boolean;
    transform?: string;
    transition?: string;
}


// ITEM GRABABLE
export const Container = styled.div<ContainerProps>`
    transform: ${props => props.isOverlay ? 'none' : props.transform};
    transition: ${props => props.isOverlay ? 'none' : props.transition};

    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    margin-left: ${props => props.isOverlay ? '20px' : `${props.level * 20 + 15}px`} !important;
    
    position: relative;
    user-select: none;
    touch-action: none;


    /* Feedback visual de arraste e overlay */
    opacity: ${props => (props.isDragging && !props.isOverlay ? 0.3 : 1)};
    z-index: ${props => (props.isOverlay ? 9 : props.isDragging ? 9 : 1)};
    cursor: ${props => (props.isOverlay ? 'grabbing' : props.isDir ? 'pointer' : 'grab')};
    
    background-color: ${props => {
        if (props.isOverlay) return '#ff1717';
        if (props.isDragging) return '#00e013';
        if (props.isOver && props.isDir) return '#e8f5e9';
        return 'transparent';
    }};

    box-shadow: ${props => props.isOverlay ? '0 5px 15px rgba(0,0,0,0.15)' : 'none'};
    border: ${props => props.isOverlay ? '1px solid #007bff' : 'none'};
    border-radius: ${props => props.isOverlay ? '4px' : '0'};
    overflow: hidden;
    
    div.box-icons {
        display: flex;
        flex-wrap: nowrap;
        justify-content: center;
        gap: 1rem;
    }


`;

export const IconBox = styled.div<{ level: number }>`
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    justify-content: center;
    gap: 1rem;

    /* Estiliza os SVGs baseados no Level */
    span.box-folder img {
        transition: all 0.2s ease;
        
        /* Se for Level 0 (Pasta Raiz), fica mais brilhante/branco */
        /* Se for Level > 0 (Arquivos internos), fica mais cinza/escuro */
        filter: ${props => props.level === 0 
            ? 'brightness(1) contrast(1.5)' 
            : 'brightness(1) contrast(1)'};
    }
`;

// ID item
export const OrderBadge = styled.span`
    font-family: "Inter", sans-serif;
    font-size:  .8rem;
    font-weight: 400;

    color: #C4C4C4;
    padding: .2rem .8rem;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: .4rem;
`;

export const ArrowIcon = styled.div<{ isOpen: boolean}>`
    display: flex;
    align-items: center;
    justify-content: center;
    width: 12px;
    transition: transform 0.2s ease-in-out;
    
    /* Gira 90 ou 180 graus dependendo da sua preferência de design */
    transform: ${props => props.isOpen ? 'rotate(180deg)' : 'rotate(0deg)'};

    img {
        width: 100%;
    }
`;

// File name and folder name
export const FileName = styled.span<{ isDir: boolean; level: number}>`
    flex: 1;
    margin-left: ${props => (props.isDir && props.level === 0 ? '1rem' : '0rem')};
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: ${props => (props.isDir ? '1rem' : '.8rem')};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;

    color: #E4E4E4;
`;

export const boxContainer = styled.div`
    display: flex;
    gap: 1rem;

    span {
        font-family: "Inter", sans-serif;
        font-size:  1rem;
        font-weight: 200;
        color: #ffffff;
        border-right: 1px solid #535A61;
        padding: 1rem;

        &:nth-child(1) {
            margin-left: 2rem;
            border-left: 1px solid #535A61;
        }
    }

    button {
        font-family: "Inter", sans-serif;
        font-size:  1rem;
        font-weight: 400;

        padding: .8rem 2rem;
        background-color: rgba(29, 96, 44, 0.33);
        color: rgba(204, 255, 215, 1);
        border-radius: .8rem;
        border: 1px solid rgba(0, 255, 58, 0.16);
    }
`;

