import styled, { keyframes } from 'styled-components';

// Tipagem dos tipos válidos de alerta no TypeScript
export type AlertType = 'success' | 'danger' | 'warning' | 'info';

// Animação de entrada deslizando da direita para a esquerda
const slideIn = keyframes`
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
`;

// Contentor fixo no canto superior direito do ecrã
export const AlertContainer = styled.div`
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

// Item individual do alerta (tipado com $tipo)
export const AlertItem = styled.div<{ $tipo: AlertType }>`
  min-width: 280px;
  padding: 12px 20px;
  border-radius: 6px;
  font-family: Arial, sans-serif;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: ${slideIn} 0.3s ease-in-out;

  /* Aplicação de cores dinâmicas baseadas no tipo de alerta */
  background-color: ${({ $tipo }) =>
    $tipo === 'success' ? '#d4edda' :
    $tipo === 'danger' ? '#f8d7da' :
    $tipo === 'warning' ? '#fff3cd' : '#d1ecf1'};

  color: ${({ $tipo }) =>
    $tipo === 'success' ? '#155724' :
    $tipo === 'danger' ? '#721c24' :
    $tipo === 'warning' ? '#856404' : '#0c5460'};

  border: 1px solid ${({ $tipo }) =>
    $tipo === 'success' ? '#c3e6cb' :
    $tipo === 'danger' ? '#f5c6cb' :
    $tipo === 'warning' ? '#ffeeba' : '#bee5eb'};
`;

// Botão de fechar (X)
export const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 20px;
  font-weight: bold;
  color: inherit;
  opacity: 0.6;
  cursor: pointer;
  margin-left: 15px;

  &:hover {
    opacity: 1;
  }
`;