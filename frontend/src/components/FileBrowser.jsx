import React, { useState, useEffect } from 'react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { Folder, FolderOpen, File, ChevronRight, X, Home, ArrowLeft } from 'lucide-react';

const FileBrowser = ({ isOpen, onClose, onSelect, initialPath = '' }) => {
    const [currentPath, setCurrentPath] = useState(initialPath);
    const [contents, setContents] = useState({ items: [], current_path: '', parent_path: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (isOpen) {
            fetchDir(currentPath);
        }
    }, [isOpen]);

    const fetchDir = async (path) => {
        setLoading(true);
        setError('');
        try {
            const res = await api.get(`/system/list-dir?path=${encodeURIComponent(path)}`);
            if (res.data.error) {
                setError(res.data.error);
            } else {
                setContents(res.data);
                setCurrentPath(res.data.current_path);
            }
        } catch (err) {
            setError('Failed to fetch directory contents.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleHome = async () => {
        try {
            const res = await api.get('/system/get-home');
            fetchDir(res.data.home);
        } catch (err) {
            console.error(err);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="file-browser-modal"
            >
                <div className="file-browser-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <FolderOpen size={20} color="#22d3ee" />
                        <span style={{ fontWeight: 'bold' }}>Server File Browser</span>
                    </div>
                    <button onClick={onClose} className="close-btn"><X size={20} /></button>
                </div>

                <div className="file-browser-toolbar">
                    <button onClick={handleHome} title="Home"><Home size={16} /></button>
                    <button
                        onClick={() => fetchDir(contents.parent_path)}
                        disabled={!contents.parent_path || contents.parent_path === contents.current_path}
                        title="Back"
                    >
                        <ArrowLeft size={16} />
                    </button>
                    <div className="current-path-display">
                        {currentPath}
                    </div>
                </div>

                <div className="file-browser-content">
                    {loading ? (
                        <div className="loading-state">Loading filesystem...</div>
                    ) : error ? (
                        <div className="error-state">{error}</div>
                    ) : (
                        <div className="items-list">
                            {contents.items.map((item, idx) => (
                                <div
                                    key={idx}
                                    className={`browser-item ${item.is_dir ? 'is-folder' : 'is-file'}`}
                                    onClick={() => item.is_dir && fetchDir(item.path)}
                                >
                                    {item.is_dir ? <Folder size={16} color="#fbbf24" /> : <File size={16} color="#94a3b8" />}
                                    <span className="item-name">{item.name}</span>
                                    {item.is_dir && <ChevronRight size={14} style={{ marginLeft: 'auto', opacity: 0.5 }} />}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="file-browser-footer">
                    <p className="footer-hint">Navigate to the folder you want to use</p>
                    <button
                        className="btn-primary"
                        style={{ width: 'auto', padding: '0.5rem 1.5rem' }}
                        onClick={() => {
                            onSelect(currentPath);
                            onClose();
                        }}
                    >
                        Select This Folder
                    </button>
                </div>
            </motion.div>

            <style jsx>{`
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.8);
                    backdrop-filter: blur(4px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                    padding: 2rem;
                }
                .file-browser-modal {
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 1rem;
                    width: 100%;
                    max-width: 700px;
                    height: 80vh;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                }
                .file-browser-header {
                    padding: 1rem;
                    border-bottom: 1px solid #334155;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: rgba(30, 41, 59, 0.5);
                }
                .close-btn {
                    background: transparent;
                    border: none;
                    color: #94a3b8;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .close-btn:hover { color: white; }
                .file-browser-toolbar {
                    padding: 0.75rem 1rem;
                    background: #0f172a;
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                    border-bottom: 1px solid #334155;
                }
                .file-browser-toolbar button {
                    background: #334155;
                    border: none;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                }
                .file-browser-toolbar button:disabled { opacity: 0.3; cursor: not-allowed; }
                .current-path-display {
                    background: rgba(0,0,0,0.3);
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 0.85rem;
                    color: #22d3ee;
                    flex: 1;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                .file-browser-content {
                    flex: 1;
                    overflow-y: auto;
                    padding: 0.5rem;
                }
                .items-list {
                    display: flex;
                    flex-direction: column;
                }
                .browser-item {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 0.75rem;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .browser-item:hover { background: rgba(255, 255, 255, 0.05); }
                .item-name {
                    font-size: 0.9rem;
                    color: #e2e8f0;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .loading-state, .error-state {
                    display: flex;
                    height: 100%;
                    align-items: center;
                    justify-content: center;
                    color: #94a3b8;
                }
                .error-state { color: #f87171; }
                .file-browser-footer {
                    padding: 1rem;
                    border-top: 1px solid #334155;
                    background: rgba(30, 41, 59, 0.5);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .footer-hint {
                    font-size: 0.8rem;
                    color: #94a3b8;
                }
            `}</style>
        </div>
    );
};

export default FileBrowser;
