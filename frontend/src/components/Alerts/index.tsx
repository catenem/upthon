import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import * as S from './style';

export interface AlertData {
  id: number;
  mensagem: string;
  tipo: S.AlertType;
}

interface AlertContextData {
  alerts: AlertData[];
  mostrarAlerta: (mensagem: string, tipo?: S.AlertType) => void;
  fecharAlerta: (id: number) => void;
}

const AlertContext = createContext<AlertContextData>({} as AlertContextData);

export const AlertProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [alerts, setAlerts] = useState<AlertData[]>([]);

  const fecharAlerta = useCallback((id: number) => {
    setAlerts((prevAlerts) => prevAlerts.filter((alerta) => alerta.id !== id));
  }, []);

  const mostrarAlerta = useCallback((mensagem: string, tipo: S.AlertType = 'info') => {
    const id = Date.now() + Math.random();
    setAlerts((prevAlerts) => [...prevAlerts, { id, mensagem, tipo }]);

    setTimeout(() => {
      fecharAlerta(id);
    }, 5000);
  }, [fecharAlerta]);

  return (
    <AlertContext.Provider value={{ alerts, mostrarAlerta, fecharAlerta }}>
      {children}
    </AlertContext.Provider>
  );
};

// Hook com verificação de segurança reforçada
export const useAlert = (): AlertContextData => {
  const context = useContext(AlertContext);

  // Se o contexto ou a lista de alertas não existir, exibe um aviso claro no console
  if (!context || !context.alerts) {
    console.error("ATENÇÃO: O hook 'useAlert' deve ser usado dentro de um 'AlertProvider'.");
    return {
      alerts: [],
      mostrarAlerta: () => {},
      fecharAlerta: () => {}
    };
  }

  return context;
};

// Componente visual dos Alertas
export const Alerts: React.FC = () => {
  const { alerts, fecharAlerta } = useAlert();

  // Prevenção extra contra erro de undefined
  if (!alerts || alerts.length === 0) return null;

  return (
    <S.AlertContainer>
      {alerts.map((alerta) => (
        <S.AlertItem key={alerta.id} $tipo={alerta.tipo}>
          <span>{alerta.mensagem}</span>
          <S.CloseButton onClick={() => fecharAlerta(alerta.id)}>
            &times;
          </S.CloseButton>
        </S.AlertItem>
      ))}
    </S.AlertContainer>
  );
};