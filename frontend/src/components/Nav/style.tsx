
import styled from 'styled-components';

// Tipagem das propriedades (props) recebidas pelo componente
interface NavProps {
    isMenuOpen: boolean;
}

export const NavContainer = styled.nav<NavProps>`
    display: grid;
    grid-template-rows: repeat(4, 1fr);
    padding: 2rem 2rem 2rem .5rem;
    /* Transição suave do tamanho do menu baseado na prop isMenuOpen */
    width: ${props => props.isMenuOpen ? '20rem' : '5rem'};
    transition: width 0.3s ease; /* Opcional: Adicionado para o menu abrir/fechar suavemente */

    a {
        position: relative;
        display: grid;
        grid-template-columns: min-content auto;
        place-items: center left;
        text-decoration: none; /* Remove o sublinhado padrão dos links */

        gap: 1.5rem;
        padding: ${props => props.isMenuOpen ? '1rem' : '1rem .4rem 1rem 1rem'};
        border-radius: 1rem;
        border: 1px solid transparent;
        transition: all 0.2s ease; /* Transição suave para as cores */
        
        /* 💡 AQUI ESTÁ A MÁGICA: 
           Aplicamos os estilos tanto quando passamos o rato (&:hover) 
           quanto quando o link está na página atual (&.active) */
        &:hover, &.active {
            border: 1px solid  #71f69013;
            background: linear-gradient(90deg, #2A323B 71%, #0E251C 100%);
            
            /* A barra vertical verde que aparece no lado direito */
            &::after {
                position: absolute;
                content: '';
                right: 0;
                display: block;
                width: .5rem;
                height: 3rem;

                background: #1F6C3B;
                border-radius: 5rem 0 0 5rem;
            }
        }

        img {
            width: 1.5rem;
        }

        span {
            display: ${props => props.isMenuOpen ? 'block' : 'none'};
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            font-weight: 300;
            line-height: 100%; /* Ajustado de 0% para 100% para evitar cortes nas letras */
            color: #FFFFFF;
            white-space: nowrap; /* Evita que o texto quebre de linha quando o menu está a fechar */
        }
    }
`;