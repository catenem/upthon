import React, { useState, useRef, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
    DndContext,
    DragEndEvent,
    PointerSensor,
    useSensor,
    useSensors,
    CollisionDetection,
    useDndMonitor,
    useDroppable,
    DragOverlay
} from '@dnd-kit/core';
import {
    SortableContext,
    verticalListSortingStrategy,
    arrayMove
} from '@dnd-kit/sortable';

import { getErrorMessage } from '../../services/api';
import { browseFolder, listFiles, moveFile, reorderFiles } from '../../services/files';
import { getPendingUploads, resumeUpload } from '../../services/uploads';
import type { FileNode } from '../../types/api';
import { FileItem } from '../../components/FileItem';
import fileBroswseSvg from '../../assets/browse-file.svg';
import equipeSvg from '../../assets/equipe.svg';
import * as S from './style';

// Importação do hook de alertas
import { useAlert } from '../../components/Alerts';

export type ModalType = 'uploader' | 'equipe' | null;

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function findNode(node: FileNode, path: string): FileNode | null {
    if (node.path === path) return node;
    for (const child of node.children ?? []) {
        const found = findNode(child, path);
        if (found) return found;
    }
    return null;
}

function parentPath(nodePath: string): string {
    const idx = nodePath.lastIndexOf('/');
    return idx > 0 ? nodePath.substring(0, idx) : nodePath;
}

function isDirectory(path: string, typeMap: Map<string, 'file' | 'directory'>): boolean {
    return typeMap.get(path) === 'directory';
}

// ─────────────────────────────────────────────────────────────────────────────
// Detecção de colisão
// O pointerWithin do dnd-kit testa TODOS os itens a cada movimento do mouse e,
// para cada um, relê a rolagem dos ancestrais. Com milhares de arquivos isso
// trava o arrasto. Aqui perguntamos ao navegador qual item está sob o ponteiro
// (custo constante) e só caímos no cálculo completo quando não há nenhum.
// ─────────────────────────────────────────────────────────────────────────────

const collisionDetection: CollisionDetection = (args) => {
    const p = args.pointerCoordinates;
    if (p) {
        for (const el of document.elementsFromPoint(p.x, p.y)) {
            const id = (el as HTMLElement).dataset?.dndId;
            const container = id !== undefined ? args.droppableContainers.find((c) => c.id === id) : undefined;
            if (container) return [{ id: container.id, data: { droppableContainer: container, value: 0 } }];
        }
    }
    // Nenhum item sob o ponteiro: vale a pasta raiz, se o ponteiro estiver dentro da área dela.
    const rootEl = document.querySelector<HTMLElement>('[data-dnd-root]');
    const rootId = rootEl?.dataset.dndId;
    const root = rootId !== undefined ? args.droppableContainers.find((c) => c.id === rootId) : undefined;
    if (p && rootEl && root) {
        const r = rootEl.getBoundingClientRect();
        if (p.x >= r.left && p.x <= r.right && p.y >= r.top && p.y <= r.bottom) {
            return [{ id: root.id, data: { droppableContainer: root, value: 0 } }];
        }
    }
    return [];
};

// ─────────────────────────────────────────────────────────────────────────────
// RootDropZone
// ─────────────────────────────────────────────────────────────────────────────

function RootDropZone({ rootPath }: { rootPath: string }) {
    const { setNodeRef, isOver } = useDroppable({ id: rootPath });
    return (
        <div
            ref={setNodeRef}
            data-dnd-id={rootPath}
            data-dnd-root=""
            style={{
                position: 'absolute',
                inset: 0,
                zIndex: 0,
                pointerEvents: 'none',
                outline: isOver ? '2px dashed #4a9eff44' : 'none',
                borderRadius: 8,
                transition: 'outline 150ms',
            }}
        />
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// FolderNode
// ─────────────────────────────────────────────────────────────────────────────

interface FolderNodeProps {
    node: FileNode;
    level: number;
    renderTree: (n: FileNode, l: number) => React.ReactElement;
    allPaths: string[];
    onOpenModal: (type: ModalType) => void;
    isModalOpen: boolean;
}

function FolderNode({ node, level, renderTree, allPaths, onOpenModal, isModalOpen }: FolderNodeProps) {
    const [isOpen, setIsOpen] = useState(false);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    useDndMonitor({
        onDragOver(event) {
            if (isModalOpen) return;

            const { over } = event;
            if (over && over.id === node.path && !isOpen) {
                if (!timerRef.current) {
                    timerRef.current = setTimeout(() => {
                        setIsOpen(true);
                        timerRef.current = null;
                    }, 600);
                }
            } else if (timerRef.current) {
                clearTimeout(timerRef.current);
                timerRef.current = null;
            }
        },
        onDragEnd() {
            if (timerRef.current) {
                clearTimeout(timerRef.current);
                timerRef.current = null;
            }
        }
    });

    return (
        <S.FolderGroup isOpen={isOpen} level={level}>
            <FileItem
                id={node.path}
                name={node.name}
                path={node.path}
                real_name={node.real_name}
                type={node.type}
                level={level}
                isOpen={isOpen}
                mp4_count={node.mp4_count}
                pdf_count={node.pdf_count}
                onOpenModal={onOpenModal}
                onClick={(e) => {
                    e.stopPropagation();
                    setIsOpen(!isOpen);
                }}
            />
            {isOpen && (
                <div className={`folder-content ${node.type}`}>
                    {node.children && node.children.length > 0 ? (
                        <SortableContext
                            items={node.children.map(c => c.path)}
                            strategy={verticalListSortingStrategy}
                        >
                            {node.children.map(child => (
                                <S.ChildWrapper
                                    key={child.path}
                                    nodeType={child.type}
                                    className={`type-${child.type}`}
                                >
                                    {renderTree(child, level + 1)}
                                </S.ChildWrapper>
                            ))}
                        </SortableContext>
                    ) : (
                        <S.EmptyFolderMessage level={level}>
                            Pasta vazia
                        </S.EmptyFolderMessage>
                    )}
                </div>
            )}
        </S.FolderGroup>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// Home
// ─────────────────────────────────────────────────────────────────────────────

interface HomeProps {
    onOpenModal: (type: ModalType) => void;
    isModalOpen: boolean;
}

export function Home({ onOpenModal, isModalOpen }: HomeProps) {
    const [pathInput, setPathInput] = useState('');
    const [fileTree, setFileTree] = useState<FileNode | null>(null);

    const [allPaths, setAllPaths] = useState<string[]>([]);
    const [typeMap, setTypeMap] = useState<Map<string, 'file' | 'directory'>>(new Map());

    const [activeId, setActiveId] = useState<string | null>(null);
    const [activeNode, setActiveNode] = useState<FileNode | null>(null);

    const [pendingUploads, setPendingUploads] = useState<string[]>([]);

    // 🔄 1. Novo Estado: Controla o carregamento do seletor de pastas
    const [browsingLoading, setBrowsingLoading] = useState(false);

    // Extração da função mostrarAlerta do nosso Contexto
    const { mostrarAlerta } = useAlert();

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
    );

    // Verifica uploads pendentes ao abrir a página
   useEffect(() => {
        const checkPendingUploads = async () => {
            try {
                const pendentes = await getPendingUploads();
                setPendingUploads(pendentes);
                console.log(`[HOME] Uploads pendentes: ${pendentes.length}`);
            } catch (error) {
                console.error("[HOME ERRO] Falha ao verificar uploads pendentes na API:", error);
                mostrarAlerta(getErrorMessage(error, "Não foi possível verificar canais pendentes."), "warning");
            }
        };
        
        checkPendingUploads();
    }, []);

    // Função para retomar o upload com alertas personalizados
    const handleResumeUpload = async (channelId: string) => {
        try {
            mostrarAlerta(`Selecione a pasta original para o canal ${channelId}.`, 'info');
            const selectedPath = await browseFolder();

            if (selectedPath) {
                await resumeUpload({ channel_id: channelId, folderPath: selectedPath });
                
                mostrarAlerta(`Retomada do canal ${channelId} iniciada com sucesso!`, 'success');
                setPendingUploads(prev => prev.filter(id => id !== channelId));
            }
        } catch (error) {
            console.error("Erro ao retomar upload:", error);
            mostrarAlerta(getErrorMessage(error, 'Falha ao tentar retomar o upload.'), 'danger');
        }
    };

    // Fetch de ficheiros
    const fetchFiles = useCallback(async (forcedPath?: string) => {
        const targetPath = forcedPath || pathInput;
        if (!targetPath) return null;

        try {
            const tree = await listFiles(targetPath);
            const paths: string[] = [];
            const map = new Map<string, 'file' | 'directory'>();

            const flatten = (node: FileNode) => {
                paths.push(node.path);
                map.set(node.path, node.type);
                node.children?.forEach(flatten);
            };
            flatten(tree);

            setAllPaths(paths);
            setTypeMap(map);
            setFileTree(tree);
            return tree;
        } catch (error) {
            mostrarAlerta(getErrorMessage(error, 'Erro ao ler diretório.'), 'danger');
            return null;
        }
    }, [pathInput, mostrarAlerta]);

    // 🔄 2. Função de Seleção de Pasta Atualizada com Gestão do Estado de Loading
    const handleBrowseAndLoad = async () => {
        setBrowsingLoading(true); // Liga o indicador de carregamento
        try {
            const selectedPath = await browseFolder();

            if (selectedPath) {
                setPathInput(selectedPath);
                const tree = await fetchFiles(selectedPath);
                
                if (tree) {
                    tree.path = selectedPath;
                    setFileTree({ ...tree });
                }
            }
        } catch (error) {
            console.error(error);
            mostrarAlerta(getErrorMessage(error, 'Erro ao selecionar a pasta.'), 'danger');
        } finally {
            setBrowsingLoading(false); // Desliga o indicador de carregamento (sucesso ou erro)
        }
    };

    // Drag handlers
    const handleDragStart = (event: any) => {
        const { active } = event;
        setActiveId(active.id as string);
        if (fileTree) setActiveNode(findNode(fileTree, active.id as string));
    };

    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;
        setActiveId(null);
        setActiveNode(null);

        if (!over || active.id === over.id) return;

        const activeIdStr = active.id as string;
        const overIdStr   = over.id   as string;
        const overIsDir = isDirectory(overIdStr, typeMap);

        try {
            if (overIsDir) {
                await moveFile(activeIdStr, overIdStr);
            } else {
                const activeParent = parentPath(activeIdStr);
                const overParent   = parentPath(overIdStr);

                if (activeParent !== overParent) {
                    await moveFile(activeIdStr, overParent);
                } else {
                    const siblings = allPaths.filter(p => {
                        if (!p.startsWith(activeParent + '/')) return false;
                        const rest = p.slice(activeParent.length + 1);
                        return !rest.includes('/'); 
                    });

                    const oldIdx = siblings.indexOf(activeIdStr);
                    const newIdx = siblings.indexOf(overIdStr);

                    if (oldIdx === -1 || newIdx === -1) return;

                    const newOrder = arrayMove(siblings, oldIdx, newIdx);
                    await reorderFiles(activeParent, newOrder);
                }
            }
            await fetchFiles();
        } catch (error) {
            mostrarAlerta(getErrorMessage(error, 'Erro na operação de movimentação.'), 'danger');
        }
    };

    const renderTree = (node: FileNode, level: number = 0): React.ReactElement =>
        node.type === 'file'
            ? (
                <FileItem
                    key={node.path}
                    id={node.path}
                    name={node.name}
                    real_name={node.real_name}
                    type="file"
                    level={level}
                    onOpenModal={onOpenModal}
                    path={node.path}
                />
            )
            : (
                <FolderNode
                    key={node.path}
                    node={node}
                    level={level}
                    renderTree={renderTree}
                    allPaths={allPaths}
                    onOpenModal={onOpenModal}
                    isModalOpen={isModalOpen}
                />
            );

    return (
        <S.Container>
            
            {/* Banner de Uploads Pendentes */}
            {pendingUploads.length > 0 && (
                <S.PendingBanner>
                    <span>
                        <strong>Atenção:</strong> Possui <b>{pendingUploads.length}</b> upload(s) pendente(s) interrompidos.
                    </span>
                    <div className="buttons-container">
                        {pendingUploads.map(id => (
                            <S.ResumeButton 
                                key={id} 
                                onClick={() => handleResumeUpload(id)}
                            >
                                Retomar Canal {id}
                            </S.ResumeButton>
                        ))}
                    </div>
                </S.PendingBanner>
            )}

            <S.Header>
                <h1>Home</h1>
                <div>
                    <p>Selecione a pasta de upload</p>
                    <div>
                        {/* 🔄 3. Botão com estado de carregamento e desabilitação durante a busca */}
                        <S.BrowseButton 
                            onClick={handleBrowseAndLoad} 
                            hasFileTree={!!fileTree}
                            disabled={browsingLoading}
                            style={{ opacity: browsingLoading ? 0.7 : 1, cursor: browsingLoading ? 'wait' : 'pointer' }}
                        >
                            <img src={fileBroswseSvg} alt="Browse" />
                            <span>
                                {browsingLoading 
                                    ? 'A carregar pasta...' 
                                    : (fileTree ? fileTree.name : 'Selecionar Pasta')
                                }
                            </span>
                        </S.BrowseButton>
                        <button className='btn-equipe' onClick={() => onOpenModal('equipe')}>
                            <img src={equipeSvg} alt="Equipe" />
                            <span>Modo Equipe</span>
                        </button>
                    </div>
                </div>
            </S.Header>

            <DndContext
                sensors={sensors}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
                collisionDetection={collisionDetection}
            >
                <S.PathFolder hasFileTree={!!fileTree}>
                    <h2>{fileTree && `../${fileTree.name}`}</h2>
                    <span>{fileTree && `(${fileTree.subfolders} sub-folder)`}</span>
                </S.PathFolder>

                <S.ExplorerContainer style={{ position: 'relative' }}>
                    {fileTree && <RootDropZone rootPath={fileTree.path} />}

                    <SortableContext items={allPaths} strategy={verticalListSortingStrategy}>
                        {fileTree?.children?.map(child => renderTree(child, 0))}
                    </SortableContext>
                </S.ExplorerContainer>

                {createPortal(
                    <DragOverlay adjustScale={false} style={{ zIndex: 10 }}>
                        {activeId && activeNode ? (
                            <FileItem
                                id={activeId}
                                name={activeNode.name}
                                real_name={activeNode.real_name}
                                type={activeNode.type}
                                level={0}
                                mp4_count={activeNode.video_count ?? activeNode.mp4_count}
                                pdf_count={activeNode.pdf_count}
                                isOverlay
                                onOpenModal={onOpenModal}
                                path={pathInput}
                            />
                        ) : null}
                    </DragOverlay>,
                    document.body
                )}
            </DndContext>
        </S.Container>
    );
}