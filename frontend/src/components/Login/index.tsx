import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logoSvg from '../../assets/logo.svg';
import axios from 'axios';
import { getErrorMessage } from '../../services/api';
import { requestLoginCode, verifyLoginCode } from '../../services/auth';
import type { RateLimitDetail } from '../../types/api';
import { Main } from './style';
// 1. Importamos o hook 'useAlert' do nosso ecossistema de alertas
import { useAlert } from '../Alerts';

export function Login() {
    const navigate = useNavigate();
    
    // 2. Extraímos a função mostrarAlerta do nosso Contexto
    const { mostrarAlerta } = useAlert();

    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const [apiId, setApiId] = useState('');
    const [apiHash, setApiHash] = useState('');
    const [password, setPassword] = useState('');
    const [phone, setPhone] = useState('');
    const [code, setCode] = useState('');

    // ETAPA 1: Solicitar o código no Telegram
    async function handleRequestCode(event: React.FormEvent) {
        event.preventDefault();
        setLoading(true);

        try {
            const result = await requestLoginCode({ api_id: apiId, api_hash: apiHash, phone });

            if (result.status === 'awaiting_code') {
                // Alerta de Sucesso
                mostrarAlerta('Código solicitado! Verifica o teu Telegram.', 'success');
                setStep(2);
            }
        } catch (error) {
            // Tratamento especial se for o bloqueio de tempo do Telegram (HTTP 429)
            if (axios.isAxiosError(error) && error.response?.status === 429) {
                const detalhe: RateLimitDetail | string = error.response.data.detail;
                const tempoTexto = typeof detalhe === 'object'
                    ? `Aguarde ${detalhe.minutos_espera} min (${detalhe.segundos_espera}s) para tentar novamente.`
                    : detalhe;

                mostrarAlerta(`Limite de tentativas atingido! ${tempoTexto}`, 'warning');
            } else {
                mostrarAlerta(getErrorMessage(error, 'Erro ao solicitar o código.'), 'danger');
            }
        } finally {
            setLoading(false);
        }
    }

    // ETAPA 2: Verificar o código e finalizar login
    async function handleVerifyCode(event: React.FormEvent) {
        event.preventDefault();
        setLoading(true);

        try {
            const result = await verifyLoginCode({ phone, code, password });

            // Se o backend solicitar verificação em duas etapas (2FA)
            if (result.status === 'needs_password') {
                setShowPassword(true);
                mostrarAlerta(result.mensagem || 'Esta conta requer verificação em duas etapas (2FA).', 'warning');
                setLoading(false);
                return;
            }

            if (result.status === 'success') {
                mostrarAlerta('Autenticado com sucesso! A redirecionar...', 'success');
                navigate('/home');
            }
        } catch (error) {
            mostrarAlerta(getErrorMessage(error, 'Erro ao validar o código informado.'), 'danger');
        } finally {
            setLoading(false);
        }
    }

    return (
        <Main>
            {step === 1 ? (
                <form onSubmit={handleRequestCode}>
                    <fieldset>
                        <legend>Bem-vindo ao Upthon!</legend>

                        <div className="field-group">
                            <label htmlFor="api-id">Api ID</label>
                            <input 
                                type="text" 
                                id="api-id" 
                                value={apiId} 
                                onChange={(e) => setApiId(e.target.value)} 
                                placeholder="Seu telegram api_id" 
                                required 
                            />
                        </div>

                        <div className="field-group">
                            <label htmlFor="api-hash">Api hash</label>
                            <input 
                                type="text" 
                                id="api-hash" 
                                value={apiHash} 
                                onChange={(e) => setApiHash(e.target.value)} 
                                placeholder="Seu telegram api_hash" 
                                required 
                            />
                        </div>

                        <div className="field-group">
                            <label>Telefone (com DDD)</label>
                            <input 
                                type="text" 
                                placeholder="+55..." 
                                value={phone} 
                                onChange={e => setPhone(e.target.value)} 
                                required 
                            />
                        </div>

                        <button type="submit" className="btn-submit" disabled={loading}>
                            {loading ? 'Enviando...' : 'Fazer login'}
                        </button>
                        <a href="https://my.telegram.org/auth">Ainda não tem as credenciais Telegram?</a>
                    </fieldset>
                </form>
            ) : (
                <form onSubmit={handleVerifyCode}>
                    <fieldset>
                        <legend>Validar Acesso</legend>
                        <p style={{ marginBottom: '1rem', color: '#666' }}>
                            Insira o código enviado para <strong>{phone}</strong>
                        </p>
                        
                        <div className="field-group">
                            <label>Código SMS</label>
                            <input
                                type="text"
                                value={code}
                                onChange={e => setCode(e.target.value)}
                                placeholder="00000"
                                required
                                autoFocus
                            />
                        </div>

                        {/* Campo de Senha 2FA condicional */}
                        {showPassword && (
                            <div className="field-group" style={{ marginTop: '1rem' }}>
                                <label>Senha de Verificação (2FA)</label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    placeholder="Sua senha do Telegram"
                                    required
                                />
                            </div>
                        )}

                        <button type="submit" className="btn-submit" disabled={loading}>
                            {loading ? 'Verificando...' : 'Finalizar Login'}
                        </button>
                        
                        <button 
                            type="button" 
                            onClick={() => { setStep(1); setShowPassword(false); }} 
                            style={{ marginTop: '10px', background: 'none', border: 'none', color: '#666', cursor: 'pointer' }}
                        >
                            Voltar e corrigir dados
                        </button>
                        
                    </fieldset>
                </form>
            )}

            <div className='logo-container'>
                <div>
                    <img src={logoSvg} alt="Logo do upthon" />
                    <p>An Ghost Industrie</p>
                </div>
            </div>
        </Main>
    );
}