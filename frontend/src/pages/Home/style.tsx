import styled from 'styled-components';
import Modal from 'react-modal';

interface FolderGroupProps {
    isOpen: boolean;
    level: number;
}

export const Container = styled.div`
    display: flex;
    flex-direction: column;
`;

// 💡 Adiciona estes componentes estilizados no teu ficheiro style.tsx

export const PendingBanner = styled.div`
    width: min-content;
    white-space: nowrap; /* Evita que o texto quebre de linha indesejadamente */
    background-color: #fff3cd;
    color: #856404;
    padding: 12px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    display: flex;
    flex-direction: column; /* Organiza o texto e a área de botões de forma limpa */
    gap: 12px;
    border: 1px solid #ffeeba;

    @media (min-width: 768px) {
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
    }

    span {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        
        strong {
            font-weight: 600;
        }

        b {
            font-weight: 700;
        }
    }

    .buttons-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
`;

export const ResumeButton = styled.button`
    background-color: #ffc107;
    color: #000000;
    border: none;
    padding: 6px 12px;
    border-radius: .4rem;
    cursor: pointer;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    font-size: .8rem;
    transition: background-color 0.2s ease, transform 0.1s ease;

    &:hover {
        background-color: #e0a800;
        transform: translateY(-1px);
    }

    &:active {
        transform: translateY(0);
    }
`;


export const Header = styled.header`
    margin-bottom: 3rem;
    div {
        display: grid;
        gap: 1rem;
        > div {
            display: flex;
            flex-wrap: nowrap;
            gap: 2rem;
        }
        p, span {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            font-weight: 200;
        }

        button {
            display: flex;
            place-content: center;
            place-items: center;
            gap: 1rem;
            max-width: 25rem;
            padding: 1rem;
            background-color: #1E2831;
            border: 1px dashed #303e4b;
            border-radius: .8rem;
            transition: all 0.2s ease;
        }

        button.btn-equipe {
            place-content: center;
            place-items: center;
            background-color: #2E77C5;
            border: 1px solid transparent;
            padding: 1rem 3rem;
        }

        span {
            display: block;
            font-weight: 400;
            color: #ffffff;
            max-width: 10rem;
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
        }

        img {
            width: 1.5rem;
        }
    }
`;

export const BrowseButton = styled.button<{ hasFileTree: boolean }>`
    background-color: ${props => props.hasFileTree ? '#ffffff' : '#ec2d2d'};
    &:hover {
        filter: brightness(1.2);
    }
`;

export const PathFolder = styled.div<{ hasFileTree: boolean}>`
    display: flex;
    place-items: center;
    flex-wrap: nowrap;
    gap: 1rem;

    h2 {
        font-family: "Inter", sans-serif;
        font-size: 1.4rem;
        max-width: 30rem;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }

    span {
        font-family: "Inter", sans-serif;
        font-size: 1rem;
        font-weight: 200;
    }
`

export const ExplorerContainer = styled.div`
    flex: 1;
    overflow-y: auto;
    min-height: 50rem;
    padding: 10px 0;

    /* Scrollbar estilizada */
    &::-webkit-scrollbar {
        width: 8px;
    }
    &::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 4px;
    }
`;

export const EmptyFolderMessage = styled.div<{ level: number }>`
    font-family: 'Inter', sans-serif;
    font-size: .8rem;
    font-weight: 200;
    color: #ffffff;
    font-style: italic;
    border: 1px dashed #eeeeee2f;
    padding: .5rem 1rem;
    border-radius: .4rem;
    margin-left: ${props => props.level * 20 + 80}px;
`;

export const FolderGroup = styled.div<FolderGroupProps>`
    display: flex;
    flex-direction: column;
    background-color: ${props =>
        props.level === 0
            ? (props.isOpen ? '#3F4A55' : '#323B43')
            : 'transparent'
    };
    border: 1px solid #3F4A55;
    border-bottom: 1px solid ${props =>
        props.level === 0
            ? (props.isOpen ? 'transparent' : '#3F4A55')
            : 'transparent'
    };
    padding-bottom: ${props => props.isOpen ? '1rem' : '0rem'};
    border-top: 1px solid ${props =>
        props.level === 0
            ? (props.isOpen ? '#62666b' : '#3F4A55')
            : 'transparent'
    };

    div.folder-content {
        margin-right: 1.5rem;
        background: #3F4A55;
    }

    &:nth-last-child(1) {
        border-radius: 0 0 .8rem .8rem;
    }
    
    &:nth-child(1) {
        border-radius: .8rem .8rem 0 0;
    }

`;

export const ChildWrapper = styled.div<{ nodeType: 'file' | 'directory' }>`
    &.type-directory {
        .type-file:nth-child(1) div {
            border-radius: .4rem .4rem 0 0;
            overflow: hidden;
        }
    }

    &.type-file {
        margin-left: 3rem;
        height: min-content;
        > div  {
            padding: .5rem 1rem;
            background-color: rgba(217, 217, 217, 0.14);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }

    }
`;


export const StyledModal = styled(Modal).attrs({
    overlayClassName: 'modal-overlay',
    className: 'modal-content',
})`
    position: absolute;
    inset: 0;
    z-index: 1000;
    display: grid;
    place-content: center;

    &.modal-content {
        background: rgba(25, 28, 31, 0.62);
        width: 100vw;
        height: 100vh;
        outline: none;
        backdrop-filter: blur(4px);
        /* Animação suave de entrada */
        animation: modalFadeIn 0.3s ease-out;
    }

    .box-content {
        position: relative;
        display: grid;
        place-content: center;
        background-color: rgba(0, 0, 0, 0.45);
        border: 1px solid #535A61;
        border-radius: 1rem;
        width: 35rem;
        padding: 3rem 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);

        form, div {
            display: grid;
        }

        form {
            label {
                font-family: 'Inter', sans-serif;
                font-size: 1.3rem;
                font-weight: 300;
                color: #E6E6E6;
                margin-bottom: .5rem;
            }
            input[type="text"] {
                background-color: #323B43;
                border: 1px solid #535A61;
                font-size: 1rem;
                padding: .8rem;
                border-radius: .8rem;
                color: #CDCDCD;
                margin-bottom: 1.5rem;
                width: 22.5rem;

                &::placeholder {
                    font-family: 'Inter', sans-serif;
                    font-size: 1rem;
                    font-weight: 200;
                    color: #CDCDCD;
                }
            }
            label span {
                
            }
            .box-type {
                border: 1px solid rgba(83, 90, 97, 0.35);
                padding: .5rem .8rem;
                border-radius: .8rem;
                width: 22.5rem;

                input {
                    position: absolute;
                    opacity: 0;
                    cursor: pointer;
                    height: 0;
                    width: 0;
                }

                .checkmark {
                    display: inline-block;
                    height: 20px;
                    width: 20px;
                    background-color: #323B43; /* O fundo que você queria */
                    border: 1px solid #535A61; /* Borda um pouco mais visível */
                    border-radius: 4px;
                    position: relative;
                    vertical-align: middle;
                    margin-right: 10px;
                    transition: all 0.2s ease;
                }

                /* Quando estiver marcado (Checked) */
                label input:checked ~ .checkmark {
                    background-color: rgba(0, 255, 58, 0.1); /* O fundo que você queria */
                    border: 1px solid rgba(0, 255, 58, 0.4);
                }

                /* O ícone de "check" (o Vzinho) - invisível por padrão */
                .checkmark:after {
                    content: "";
                    position: absolute;
                    display: none;
                    left: 6px;
                    top: 2px;
                    width: 5px;
                    height: 10px;
                    border: solid rgba(223, 255, 230, 1);
                    border-width: 0 2px 2px 0;
                    transform: rotate(45deg);
                }

                /* Mostra o check quando o input for marcado */
                label input:checked ~ .checkmark:after {
                    display: block;
                }

            }
        }
    }

    button[type="submit"] {
        display: grid;
        place-content: center;
        font-family: 'Inter', sans-serif;
        font-size: 1.3rem;
        font-weight: 300;
        color: #fff;
        padding: 1rem 2rem;
        width: 22.5rem;
        background-color: rgba(0, 255, 58, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.28);
        border-radius: 1rem;
        margin-top: 1.5rem;
    }

    @keyframes modalFadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }

  /* Estilização de Elementos Internos */
    h2 {
        font-family: 'Inter', sans-serif;
        font-size: 1.8rem;
        margin-bottom: 1.5rem;
        color: #fff;
    }

    .btn-close {
        position: absolute;
        top: 0px;
        right: 0px;
        padding: 1.5rem 1rem;
        background: transparent;
        border: none;
        color: #7c7c8a;

        display: flex;
        align-items: center;
        justify-content: center;


        .icon-x {
            position: relative;
            width: 20px;
            height: 2px;
            background-color: #7c7c8a;
            display: block;
            transform: rotate(45deg);
            transition: transform 0.3s ease, background-color 0.3s ease;
        }

        .icon-x::after {
            content: "";
            position: absolute;
            width: 20px;
            height: 2px;
            background-color: inherit;
            display: block;
            transform: rotate(90deg);
            top: 0;
            left: 0;
        }

        /* Efeito Hover */
        &:hover .icon-x {
            background-color: #e2808090;
            transform: rotate(135deg);
        }
    }
`;

export const ModalButton = styled.button<{ variant?: 'primary' | 'ghost' }>`
  padding: 10px 20px;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid ${props => props.variant === 'primary' ? '#007bff' : '#3d464d'};
  background: ${props => props.variant === 'primary' ? '#007bff' : 'transparent'};
  color: #fff;

  &:hover {
    filter: brightness(1.1);
    background: ${props => props.variant === 'primary' ? '#0069d9' : '#3d464d'};
  }

  &:active {
    transform: scale(0.98);
  }
`;

export const CloseIcon = styled.button`
  position: absolute;
  top: 15px;
  right: 15px;
  background: transparent;
  border: none;
  color: #7c7c8a;
  font-size: 1.2rem;
  cursor: pointer;
  &:hover { color: #fff; }
`;