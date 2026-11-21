import React, { useState, useTransition, memo } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Router } from './routes';
import { GlobalStyle } from './styles/global';
import { getErrorMessage } from './services/api';
import { getPendingUploads, resumeUpload, startUpload } from './services/uploads';
// Importação do ecossistema de alertas
import { AlertProvider, Alerts, useAlert } from './components/Alerts';
import * as H from './pages/Home/style';

type ModalType = 'uploader' | 'equipe' | null;

// 💡 OTIMIZAÇÃO 1: Memoizamos o Router.
// Isto impede que a página de fundo (Home e a sua árvore de ficheiros) seja re-renderizada
// desnecessariamente quando o estado do modal muda.
const MemoizedRouter = memo(Router);

export function App() {
    const [activeModal, setActiveModal] = useState<ModalType>(null);
    const [modalData, setModalData] = useState<any>(null);
    
    const [pendingUploads, setPendingUploads] = useState<string[]>([]);
    const [selectedPendingId, setSelectedPendingId] = useState<string>('');

    // 💡 OTIMIZAÇÃO 2: Hook useTransition do React 18.
    // Permite fazer atualizações de estado sem bloquear a resposta imediata do clique.
    const [, startTransition] = useTransition();

    // Função para buscar os uploads pendentes na API
    const fetchPendingUploads = async () => {
        try {
            setPendingUploads(await getPendingUploads());
        } catch (error) {
            console.error("Erro ao buscar pendências:", error);
        }
    };

    const openModal = (type: ModalType, data?: any) => {
        // Envolvemos a alteração do modal em startTransition para priorizar a resposta ao clique
        startTransition(() => {
            setModalData(data);
            setActiveModal(type);
            setSelectedPendingId('');
        });
        
        // Dispara a requisição em segundo plano sem travar a abertura visual do modal
        if (type === 'uploader') {
            fetchPendingUploads();
        }
    };

    const closeModal = () => {
        startTransition(() => {
            setActiveModal(null);
            setModalData(null);
            setSelectedPendingId('');
        });
    };

    return (
        <BrowserRouter>
            {/* O AlertProvider envolve toda a aplicação */}
            <AlertProvider>
                {/* Componente fixo de alertas */}
                <Alerts />
                
                <InnerApp 
                    activeModal={activeModal}
                    modalData={modalData}
                    pendingUploads={pendingUploads}
                    selectedPendingId={selectedPendingId}
                    setSelectedPendingId={setSelectedPendingId}
                    openModal={openModal}
                    closeModal={closeModal}
                />
            </AlertProvider>
        </BrowserRouter>
    );
}

// Componente interno auxiliar para consumo do hook useAlert
function InnerApp({ 
    activeModal, 
    modalData, 
    pendingUploads, 
    selectedPendingId, 
    setSelectedPendingId, 
    openModal, 
    closeModal 
}: any) {
    const { mostrarAlerta } = useAlert();

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        const formData = new FormData(e.currentTarget);
        
        if (!modalData?.path) {
            mostrarAlerta("Erro: Caminho da pasta não encontrado.", "danger");
            console.error("modalData está incompleto:", modalData);
            return;
        }

        try {
            if (selectedPendingId !== '') {
                // Fluxo de Retomada (Resume)
                const payloadResume = {
                    channel_id: selectedPendingId,
                    folderPath: modalData.path,
                    is_topics: formData.get('typeChannel') === 'topic' 
                };

                await resumeUpload(payloadResume);
                mostrarAlerta("Retomada iniciada com sucesso!", "success");

            } else {
                // Fluxo de Novo Canal (Start)
                const channelName = String(formData.get('channelName') ?? '').trim();
                if (!channelName) {
                    mostrarAlerta('Informe o nome do canal.', 'warning');
                    return;
                }

                await startUpload({
                    channelName,
                    typeChannel: String(formData.get('typeChannel') ?? 'topic'),
                    folderPath: modalData.path,
                    folderName: modalData.name
                });
                mostrarAlerta("Upload iniciado com sucesso!", "success");
            }
            
            closeModal();
        } catch (error) {
            mostrarAlerta(getErrorMessage(error, "Erro ao processar a operação."), "danger");
            console.error(error);
        }
    };

    return (
        <>
            {/* 💡 O MemoizedRouter evita re-renderizar as páginas quando o modal abre */}
            <MemoizedRouter onOpenModal={openModal} isModalOpen={!!activeModal} />
            <GlobalStyle />

            <H.StyledModal
                isOpen={!!activeModal}
                onRequestClose={closeModal}
            >
                {activeModal === 'uploader' && (
                    <div className='box-content'>
                        <button onClick={closeModal} className='btn-close'><span className="icon-x"></span></button>
                        <h2>Configurações de Upload</h2>
                        
                        <form onSubmit={handleSubmit}>
                            
                            {pendingUploads.length > 0 && (
                                <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#fff3cd', borderRadius: '8px' }}>
                                    <label htmlFor="resumeChannel" style={{ color: '#856404', fontWeight: 'bold' }}>
                                        ⚠️ Detetamos uploads pendentes. Deseja retomar algum?
                                    </label>
                                    <select 
                                        id="resumeChannel" 
                                        value={selectedPendingId}
                                        onChange={(e) => setSelectedPendingId(e.target.value)}
                                        style={{ width: '100%', padding: '8px', marginTop: '5px' }}
                                    >
                                        <option value="">Não, quero criar um canal novo</option>
                                        {pendingUploads.map((id: string) => (
                                            <option key={id} value={id}>Retomar Canal: {id}</option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            <label htmlFor="channelName" style={{ opacity: selectedPendingId ? 0.5 : 1 }}>
                                Nome do Novo Canal
                            </label>
                            <input
                                type="text"
                                id="channelName"
                                name="channelName"
                                defaultValue={modalData?.name || ''}
                                placeholder={modalData?.name || 'Digite o nome do canal'}
                                disabled={selectedPendingId !== ''}
                                style={{ opacity: selectedPendingId ? 0.5 : 1 }}
                            />

                            <label htmlFor="typeChannel">Tipo de Canal</label>
                            <div className='box-type'>
                                <label>
                                    <input type="radio" name="typeChannel" value="private" />
                                    <span className="checkmark"></span>
                                    Canal privado
                                </label>
                                <label>
                                    <input type="radio" name="typeChannel" value="topic" defaultChecked />
                                    <span className="checkmark"></span>
                                    Super Grupo (Topics)
                                </label>
                            </div>

                            <button type="submit">
                                {selectedPendingId ? 'Retomar Upload' : 'Iniciar Upload'}
                            </button>
                        </form>
                    </div>
                )}

                {activeModal === 'equipe' && (
                    <div className='box-content'>
                        <button onClick={closeModal} className='btn-close'><span className="icon-x"></span></button>
                        <h2>👥 Modo Equipe</h2>
                        <p>Configure as permissões dos colaboradores.</p>
                    </div>
                )}
            </H.StyledModal>
        </>
    );
}