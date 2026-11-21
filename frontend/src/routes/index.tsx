import { Routes, Route, Navigate } from 'react-router-dom';
import { Login } from '../components/Login';
import { Home } from '../pages/Home';
import { Dashboard } from '../pages/Dashboard';
import { Settings } from '../pages/Settings';
import { Bots } from '../pages/Bots';
import { DefaultLayout } from '../components/Layout';

// 1. Definição do tipo de modal que o sistema aceita
export type ModalType = 'uploader' | 'equipe' | null;

// 2. Interface de propriedades do Router
interface RouterProps {
  onOpenModal: (type: ModalType, data?: any) => void;
  isModalOpen: boolean;
}

export function Router({ onOpenModal, isModalOpen }: RouterProps) {
  // A verificação de login automática e o estado "loading" foram removidos.
  // Agora o sistema renderiza as rotas imediatamente, permitindo acesso livre.

  return (
    <Routes>
      {/* Rota de Login (mantida caso o utilizador queira aceder manualmente) */}
      <Route path="/login" element={<Login />} />

      {/* Rotas da Aplicação (agora acessíveis diretamente sem bloqueio) */}
      <Route path="/" element={<DefaultLayout />}>
        
        {/* Rota da Home com as propriedades do Modal */}
        <Route 
          path="/home" 
          element={
            <Home 
              onOpenModal={onOpenModal} 
              isModalOpen={isModalOpen} 
            />
          } 
        />
        
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/bots" element={<Bots />} />

        {/* Sempre que acederem à raiz "/", são redirecionados automaticamente para "/home" */}
        <Route path="/" element={<Navigate to="/home" />} />
      </Route>
    </Routes>
  );
}