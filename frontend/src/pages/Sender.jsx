import React, { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Upload, Lock, CheckCircle, AlertCircle, Folder, FileVideo, FileText } from 'lucide-react';

const Sender = () => {
    const [faceFile, setFaceFile] = useState(null);
    const [targetDir, setTargetDir] = useState('');
    const [secretText, setSecretText] = useState('');
    const [secretFiles, setSecretFiles] = useState([]);

    const [status, setStatus] = useState({ type: '', msg: '' });
    const [loading, setLoading] = useState(false);

    const handleFaceChange = (e) => setFaceFile(e.target.files[0]);

    const handleFilesChange = (e) => {
        setSecretFiles(Array.from(e.target.files));
    };

    const handleCreateVault = async () => {
        if (!faceFile) return setStatus({ type: 'error', msg: 'Face image is required.' });
        if (!targetDir) return setStatus({ type: 'error', msg: 'Target directory path is required.' });
        if (!secretText && secretFiles.length === 0) return setStatus({ type: 'error', msg: 'Add a message or files to encrypt.' });

        setLoading(true);
        setStatus({ type: '', msg: '' });

        const formData = new FormData();
        formData.append('target_dir', targetDir);
        formData.append('reference_image', faceFile);
        if (secretText) formData.append('secret_text', secretText);

        secretFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const res = await axios.post('http://localhost:8000/api/vault/create', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setStatus({ type: 'success', msg: res.data.message });
        } catch (err) {
            console.error(err);
            setStatus({ type: 'error', msg: err.response?.data?.detail || 'Vault creation failed.' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container-center">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel"
            >
                <header>
                    <h1 className="title-gradient">Create Secure Vault</h1>
                    <p className="subtitle">Deploy an encrypted vault to a Pendrive/Folder</p>
                </header>

                <div className="grid-2">
                    {/* Left Col: Config */}
                    <div>
                        {/* 1. Target Directory */}
                        <div className="form-group">
                            <label className="section-header">
                                <Folder size={16} color="#22d3ee" /> Target Directory Path
                            </label>
                            <input
                                type="text"
                                value={targetDir}
                                onChange={(e) => setTargetDir(e.target.value)}
                                placeholder="Select a directory..."
                                className="input-field"
                                readOnly
                                style={{ cursor: 'pointer', background: '#0f172a' }}
                                onClick={async () => {
                                    try {
                                        const res = await axios.post('http://localhost:8000/api/system/browse');
                                        if (res.data.path) setTargetDir(res.data.path);
                                    } catch (e) {
                                        console.error(e);
                                    }
                                }}
                            />
                            <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>path to external drive</p>
                            <button
                                onClick={async () => {
                                    try {
                                        const res = await axios.post('http://localhost:8000/api/system/browse');
                                        if (res.data.path) setTargetDir(res.data.path);
                                    } catch (e) {
                                        console.error(e);
                                    }
                                }}
                                className="btn-small"
                                style={{ marginTop: '0.5rem', background: '#334155' }}
                            >
                                Browse System...
                            </button>
                        </div>

                        {/* 2. Face Enrollment */}
                        <div className="form-group">
                            <label className="section-header">
                                <Upload size={16} color="#c084fc" /> Authorized Face
                            </label>
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleFaceChange}
                                className="input-field"
                            />
                        </div>
                    </div>

                    {/* Right Col: Content */}
                    <div className="form-group">
                        <label className="section-header">
                            <Lock size={16} color="#4ade80" /> Secret Content
                        </label>

                        <textarea
                            value={secretText}
                            onChange={(e) => setSecretText(e.target.value)}
                            placeholder="Secret Text Message..."
                            className="textarea-field"
                            rows={4}
                        />

                        <div style={{ borderTop: '1px solid #334155', paddingTop: '1rem', marginTop: '1rem' }}>
                            <label className="section-header">
                                <FileVideo size={16} color="#94a3b8" /> Attach Files
                            </label>
                            <input
                                type="file"
                                multiple
                                onChange={handleFilesChange}
                                className="input-field"
                            />
                            <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                                {secretFiles.map((f, i) => (
                                    <span key={i} style={{ fontSize: '0.75rem', background: '#334155', padding: '2px 4px', borderRadius: '4px' }}>
                                        {f.name}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                <div style={{ marginTop: '1.5rem' }}>
                    <button
                        onClick={handleCreateVault}
                        disabled={loading}
                        className="btn-primary"
                    >
                        {loading ? 'Encrypting & Generating Vault...' : 'Secure & Save Vault'}
                    </button>
                </div>

                {status.msg && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className={`alert ${status.type === 'success' ? 'alert-success' : 'alert-error'}`}
                    >
                        {status.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                        <span>{status.msg}</span>
                    </motion.div>
                )}
            </motion.div>
        </div>
    );
};

export default Sender;
