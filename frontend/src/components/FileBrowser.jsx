import React, { useState, useEffect } from 'react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { Folder, FolderOpen, File, ChevronRight, X, Home, ArrowLeft, HardDrive } from 'lucide-react';

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
            const url = path ? `/system/list-dir?path=${encodeURIComponent(path)}` : '/system/list-dir';
            const res = await api.get(url);
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
                        disabled={!contents.parent_path}
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
                                    {item.is_drive ? <HardDrive size={16} color="#38bdf8" /> :
                                        item.is_dir ? <Folder size={16} color="#fbbf24" /> :
                                            <File size={16} color="#94a3b8" />}
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
        </div>
    );
};

export default FileBrowser;
