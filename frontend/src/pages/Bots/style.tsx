import styled from 'styled-components';

export const Form = styled.form`
    label {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        font-weight: 400;
        color: #fff;
    }
    div {
      margin-top: .8rem;
      display: flex;
      gap: 1rem;

      input {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 200;
        color: #fff;

        background: none;
        padding: .4rem 1rem;
        border: 1px solid  #ffffff5b;
        border-radius: .4rem;
        width: 15rem;

        &::placeholder {
          color: #fff;
          font-size: .8rem;
        }
      }

      button {
        background:  #47FF71;
        padding: 0 1rem;
        border-radius: .4rem;

        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 500;
        color: #071604;
      }
    }

`;

export const BotList = styled.div`
  margin-top: 3rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;

  .bot-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid #ffffff0d;
    padding: 1rem;
    border-radius: 1.2rem;
    display: grid;
    grid-template-columns: 5rem 1fr;
    
    gap: .5rem;

    transition: transform 0.3s, background 0.3s;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 2px;
      background: linear-gradient(90deg, transparent, #4a9eff, transparent);
      opacity: 0;
      transition: opacity 0.3s;
    }

    &:hover {
      background: rgba(255, 255, 255, 0.05);
      transform: translateY(-5px);
      
      &::before {
        opacity: 1;
      }
    }

    img {
      width: 4rem;
      border-radius: 50%;
      border: 1px solid #ffffff0d;;
    }

    div {
      display: grid;
      gap: .2rem;
      
      justify-items: left;
      
      p {
        color: #fffdfd;
        font-family: "Inter", sans-serif;
        font-size: 1.2rem;
        font-weigth:  400;
        word-break: break-all;
      }

      span {
        font-family: "Inter", sans-serif;
        font-size: .8rem;
        font-weight: 500;
        color: #b1b0b0;
      }
    }
  }
`;