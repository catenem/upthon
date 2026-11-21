import styled from 'styled-components';

export const Container = styled.div`
  h2 {
    font-family: "Inter", sans-serif;
    font-size: 1.4rem;
    font-weight: 600;

    margin-bottom: 1rem;
  }
`;

export const SummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 300px));
  gap: 16px;
  margin-bottom: 24px;
`;

export const Card = styled.div`
  display: flex;
  justify-content: space-between;
  border-radius: 8px;
  border: 1px solid #3F3F3F;
  cursor: pointer;

  &:hover {
    transform: scale(1.01);
  }
  
  &.bars {
    box-shadow: 0rem 0rem 1rem rgba(0, 255, 58, 0.1);
  }

  &.sent {
    box-shadow: 0rem 0rem 1rem #2A0947;
  }

  &.clock {
    box-shadow: 0rem 0rem 1rem rgba(228, 218, 113, 0.2);
  }

  div:nth-child(1) {
    padding: 1rem;

    h3 {
      font-size: 1rem;
      font-weight: 100;
      font-family: '', sans-serif;
      color: #ffffff;
      white-space: nowrap;
    }

    p.value {
      font-family: '', sans-serif;
      font-size: 1.6rem;
      font-weight: 600;
      color: #ffffff;
    }
  }

  div:nth-child(2) {
    display: grid;
    border-radius: 50% .4rem .4rem 50%;
    padding: 1rem 1rem 1rem 2rem;
    place-content: center;
    img {
      justify-self: right;
    }
  }

  div.bars {
    background: linear-gradient(-130deg, #18412F 0%, #17262B 100%);
  }

  div.sent {
     background: linear-gradient(-130deg, #3F1E67 0%, #17262B 100%);
  }

  div.clock {
     background: linear-gradient(-130deg, #838329 0%, #17262B 100%);
  }
`;

export const ProgressSection = styled.div`

`;

export const HeaderSection = styled.div`
  display: grid;
  gap: 1rem;
  margin-bottom: 2rem;

  h1 {
    margin-bottom: 0;
  }
`;

export const FilterBox = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;

  select {
    background-color: rgba(0, 0, 0, 0.1);
    color: #fffffff1;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: .8rem 1rem;
    border-radius: .4rem;
    font-family: '', sans-serif;
    font-size: 1rem;
    cursor: pointer;
    outline: none;
    transition: border-color 0.2s ease;

    &:hover, &:focus {
      border-color: #ffffff;
    }

    option {
      background-color: #1e1e2e;
      color: #cdd6f4;
    }
  }
`;

// Adicionar ao style.ts

export const TableContainer = styled.div`
  width: 100%;
  overflow-x: auto;
  max-height: 450px;
  overflow-y: auto;
  border-radius: .4rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

export const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-family: '', sans-serif;

  thead {
    background-color: rgba(0, 0, 0, 0.5);
    position: sticky;
    top: 0;
    z-index: 1;

    th {
      padding: 12px 16px;
      color: #ffffff;
      font-weight:400;
      font-size: 1.2rem;
      border-bottom: 2px solid #313244;
      white-space: nowrap;
    }
  }

  tbody {
    tr {
      border-bottom: 1px solid #313244;
      transition: background-color 0.15s ease;

      &:hover {
        background-color: #2b2b3d;
      }

      td {
        padding: 12px 16px;
        color: #cdd6f4;

        &.file-name {
          font-weight: 500;
          color: #89b4fa;
        }
      }
    }
  }
`;

export const StatusBadge = styled.span<{ isSent: boolean }>`
  display: inline-block;
  padding: 0rem 1rem;
  border-radius: .4rem;
  font-size: 1rem;
  font-weight: 100;
  background-color: ${({ isSent }) => (isSent ? 'rgba(166, 227, 161, 0.15)' : 'rgba(249, 226, 175, 0.15)')};
  color: ${({ isSent }) => (isSent ? '#a6e3a1' : '#f9e2af')};
  border: 1px solid ${({ isSent }) => (isSent ? '#b8ffb24b' : '#f9e1af57')};
`;