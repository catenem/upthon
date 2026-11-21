import styled from 'styled-components';

interface HeaderProps {
    isMenuOpen: boolean;
}

export const HeaderContainer = styled.header<HeaderProps>`
    --sz-profile-img: ${props => props.isMenuOpen ? '4.5rem' : '3rem'};
    
    display: grid;
    width: ${props => props.isMenuOpen ? '20rem' : '5rem'};
    background: #0E1621;
    height: 100vh;
    overflow: hidden;

    .box-logo {
        width: 100%;
        display: flex;
        flex-wrap: nowrap;
        justify-content: space-between;
        place-items: center;
        padding: ${props => props.isMenuOpen ? '1rem 2rem' : '1rem'};

        img {
            display: ${props => props.isMenuOpen ? 'block' : 'none'};
            width: 10rem;
            height: fit-content;
        }

        button {
            padding: .5rem .5rem .5rem .2rem;
            background: none;
            border-radius: .4rem;
            border: 2px solid #262D37;
            cursor: pointer;
            width: 3rem;
            height: 3rem;

            svg {
                width: 1.8rem;
                height: 1.8rem;
                transform: ${props => props.isMenuOpen ? 'rotate(0deg)' : 'rotate(180deg)'};
                transition: transform 0.3s ease;
            }
        }
    }

    .box-user {
        display: grid;
        grid-template-columns: 1fr 3fr;
        grid-template-areas:
            "top-left top-rigth"
            "bottom bottom";
        padding: ${props => props.isMenuOpen ? '2rem 2rem 1rem 2rem' : '1rem'};
        border-top: 1px solid #262D37;
        border-bottom: 1px solid #262D37;

        .profile {
            display: grid;
            grid-area: top-left;
            grid-template-rows: ${props => props.isMenuOpen ? '1fr .5fr' : '1fr'};
            place-items: center;
            justify-self: top;
            gap: 1rem;

            img {
                width: var(--sz-profile-img);
                height: var(--sz-profile-img);
                border-radius: 50%;
                object-fit: cover;
                border: 1px solid #262D37;
            }

            p {
                display: ${props => props.isMenuOpen ? 'block' : 'none'};
                font-family: 'Inter', sans-serif;
                font-size: 1rem;
                white-space: nowrap;

                a {
                    font-family: sans-serif;
                    display: block;
                    color: #206ee2;
                    padding: .4rem .8rem;
                    border-radius: .8rem;
                }
            }
        }
    }
`

export const DropDownButton = styled.div<HeaderProps & { isOpen: boolean }>`
    grid-area: top-rigth;
    display: ${props => props.isMenuOpen ? 'grid' : 'none'};
    justify-self: top;
    align-items: end;
    padding: 1rem;

    button {
        width: fit-content;
        height: fit-content;
        justify-self: end;
        background: transparent;
        border: none;

        svg {
            width: 1.2rem;
            height: 1.2rem;
            transform: ${props => props.isOpen ? 'none' : 'rotate(180deg)'};
            transition: transform 0.3s;
        }
    }
`

export const DropDownContent = styled.div<HeaderProps & { isOpen: boolean }>`
    grid-area: bottom;
    border: 1px solid green;
    display: ${props => !props.isMenuOpen ? 'none' : props.isOpen ? 'grid' : 'none'};
`