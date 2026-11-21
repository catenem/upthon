import { createGlobalStyle } from "styled-components";

export const GlobalStyle = createGlobalStyle`
    :root {
        -webkit-font-smoothing: antialiased;
        color: #FDFDFD;
    }

    *, *::before, *::after {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    #root {
        display: grid;
        grid-template-columns: min-content auto;
        overflow: hidden;
        height: 100vh;
        width: 100vw;
    }

    main {
        height: 100%;
        overflow-y: scroll;
        padding: 1rem;
    }

    body {
        position: relative;
        background: #17212B;
    }

    a {
        text-decoration: none;
    }

    fieldset {
        border: none;
    }

    button {
        cursor: pointer;
        background: none;
        border: none;
    }

    h1 {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        margin-bottom: 2rem;
    }

    [disabled] {
        opacity: 0.6;
        cursor: not-allowed;
    }

    @media (max-width: 1080px) {
        :root {
            font-size: 93.75%;
        }
    }

    @media (max-width: 720px) {
        :root {
            font-size: 87.5%;
        }
    }

    @media (max-width: 480px) {
        :root {
            font-size: 80%;
        }
    }
`