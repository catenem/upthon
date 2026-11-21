import styled from 'styled-components';
import loginBg from '../../assets/login-bg.svg';


export const Main = styled.main`
    display: grid;
    grid-template-columns: 1fr 1fr;
    place-items: center;
    width: 100vw;

    min-height: 100vh;
    background: #ffffff;
    padding: 0;

    form {
        fieldset {
            display: grid;
            gap: 1rem;
        }

        legend {
            font-family: 'Poppins', sans-serif;
            font-size: 2.3rem;
            font-weight: 700;
            color: hsl(0, 0%, 0%);

            margin-bottom: 3rem
        }

        .field-group {
            display: grid;
            grid-template-rows: auto auto;

            label {
                font-family: 'Inter', sans-serif;
                font-size: 1.3rem;
                font-weight: 600;
                color: hsl(213.33333333333334, 13.846153846153852%, 12.745098039215685%);
                padding: 1rem 1rem .5rem .5rem;
            }

            input {
                padding: 1rem;
                font-family: 'Inter', sans-serif;
                font-size: 1rem;

                color: #030805;

                border: 1px solid #adadad85;
                border-radius: 1rem;

                &::placeholder {
                    font-family: 'Inter', sans-serif;
                    font-size: 1rem;
                    color: #ADADAD;
                } 

                & :focus {
                    outline: 1px solid #05260C;
                }
            }
        }

        button[type="submit"] {
            margin-top: 3rem;
            padding: 1.2rem 1rem;
            border-radius: 1rem;
            border: 1px solid #A6A6A6;

            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            font-weight: 600;
            color: hsl(0, 0%, 100%);
            box-shadow: 0rem 0.5rem 1rem rgba(71, 255, 113, 0.3);
            
            background: linear-gradient(135deg, #47FF71 0%, #1d6b2f 50%, #1d6b2f 100%);
            background-size: 250% 250%;
            background-position: 100% 100%;
            transition: all 400ms ease-in-out;
        }

        button[type="submit"]:hover {
            background-position: 0% 0%;
            box-shadow: 0rem 0.5rem 1.5rem rgba(71, 255, 113, 0.5); 
        }

        a {
            font-family: "Inter", sans-serif;
            font-size: .8rem;
            color: #215eb9;
            justify-self: center;
        }
    }

    .logo-container {
        position: relative;
        display: grid;
        place-content: center;
        width: 100%;
        height: 100%;
        background: url(${loginBg});
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;

        > div {
            display: grid;
            place-content: center;
            place-items: center;

            img {
                position: relative;
            }
            P {
                font-family: "Inter";
                font-size: .8rem;
            }
        }
    }
    @media (max-width: 900px) {
        grid-template-columns: 1fr;

        .logo-container {
            display: none;
        }
    }
`