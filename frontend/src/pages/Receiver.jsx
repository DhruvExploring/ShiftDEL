import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Unlock, AlertTriangle, RefreshCw, FolderOpen, Play, FileText, Image as ImageIcon, Lock, FileVideo, Search } from 'lucide-react';
import FileBrowser from '../components/FileBrowser';

const Receiver = () => {
    const webcamRef = useRef(null);
    const [sourceDir, setSourceDir] = useState('');
    const [decryptedFiles, setDecryptedFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [failCount, setFailCount] = useState(0);
    const [isBrowserOpen, setIsBrowserOpen] = useState(false);
    const objectUrlsRef = useRef([]);

    // Helper to convert base64 to Blob URL
    const createSafeUrl = (base64, mimeType) => {
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: mimeType });
        const url = URL.createObjectURL(blob);
        objectUrlsRef.current.push(url);
        return url;
    };

    // Helper for UTF-8 safe base64 decoding
    const decodeBase64UTF8 = (base64) => {
        return decodeURIComponent(atob(base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
    };

    // Cleanup object URLs on unmount or before new results
    const cleanupUrls = () => {
        objectUrlsRef.current.forEach(url => URL.revokeObjectURL(url));
        objectUrlsRef.current = [];
    };

    React.useEffect(() => {
        return cleanupUrls;
    }, []);

    const captureAndUnlock = useCallback(async () => {
        if (!webcamRef.current || !sourceDir) {
            setError('Please enter source path and ensure camera is ready.');
            return;
        }

        setLoading(true);
        setError('');
        cleanupUrls();
        setDecryptedFiles([]);

        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) {
            setLoading(false);
            return;
        }

        const blob = await fetch(imageSrc).then(res => res.blob());
        const formData = new FormData();
        formData.append('face_image', blob, 'capture.jpg');
        formData.append('source_dir', sourceDir);

        try {
            const res = await api.post('/vault/unlock', formData);
            if (res.data.success) {
                // Pre-calculate URLs
                const filesWithUrls = res.data.files.map(f => ({
                    ...f,
                    blobUrl: createSafeUrl(f.content, f.type)
                }));
                setDecryptedFiles(filesWithUrls);
                setFailCount(0);
            }
        } catch (err) {
            console.error(err);
            const detail = err.response?.data?.detail || 'Verification failed.';

            // Extract fail count if returned by backend (via relay)
            if (err.response?.status === 403 && detail.includes("VAULT DESTROYED")) {
                setFailCount(3);
                setError("VAULT DESTROYED: Maximum attempts exceeded.");
            } else {
                setFailCount(prev => prev + 1);
                setError(detail);
            }
        } finally {
            setLoading(false);
        }
    }, [webcamRef, sourceDir]);

    if (failCount >= 3) {
        return (
            <div className="container-center" style={{ background: '#450a0a' }}>
                <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className="glass-panel" style={{ textAlign: 'center', borderColor: '#ef4444' }}>
                    <AlertTriangle size={80} color="#ef4444" style={{ margin: '0 auto' }} />
                    <h1 style={{ color: '#f87171', fontSize: '3rem', margin: '1rem 0' }}>VAULT DESTROYED</h1>
                    <p style={{ color: '#fca5a5' }}>Security protocol initiated. Secure files have been overwritten and deleted from the source drive.</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="btn-primary"
                        style={{ marginTop: '2rem', background: '#7f1d1d' }}
                    >
                        Reset Application
                    </button>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="container-center">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-panel large"
                style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}
            >
                <header>
                    <h1 className="title-gradient">Vault Access Terminal</h1>
                    <p className="subtitle">Target Source Drive for Decryption</p>
                </header>

                <div className="grid-2">
                    {/* Left: Input & Webcam */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="webcam-wrapper">
                            {!decryptedFiles.length ? (
                                <Webcam
                                    audio={false}
                                    ref={webcamRef}
                                    screenshotFormat="image/jpeg"
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                    videoConstraints={{ facingMode: "user" }}
                                />
                            ) : (
                                <div style={{ color: '#4ade80', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                    <ShieldCheck size={48} />
                                    <span style={{ fontWeight: 'bold', marginTop: '0.5rem' }}>Authenticated</span>
                                </div>
                            )}
                            <div className="live-indicator">
                                <div className="pulse-dot" /> Live
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="section-header">
                                <FolderOpen size={14} color="#94a3b8" /> Source Directory
                            </label>
                            <input
                                type="text"
                                value={sourceDir}
                                onChange={(e) => setSourceDir(e.target.value)}
                                onClick={() => !decryptedFiles.length && setIsBrowserOpen(true)}
                                placeholder="Enter or select a directory..."
                                disabled={decryptedFiles.length > 0}
                                className="input-field"
                                style={{ background: '#0f172a' }}
                            />
                            <button
                                onClick={() => setIsBrowserOpen(true)}
                                className="btn-small"
                                style={{ marginTop: '0.5rem', background: '#334155', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
                                disabled={decryptedFiles.length > 0}
                            >
                                <Search size={14} /> Browse Server Directories...
                            </button>

                            <FileBrowser
                                isOpen={isBrowserOpen}
                                onClose={() => setIsBrowserOpen(false)}
                                onSelect={(path) => setSourceDir(path)}
                                initialPath={sourceDir}
                            />

                            {!decryptedFiles.length && (
                                <button
                                    onClick={captureAndUnlock}
                                    disabled={loading || !sourceDir}
                                    className="btn-primary"
                                    style={{ marginTop: '1rem' }}
                                >
                                    {loading ? <RefreshCw className="animate-spin" size={16} /> : <Unlock size={16} />}
                                    {loading ? 'Verifying...' : 'Unlock Vault'}
                                </button>
                            )}

                            {error && (
                                <div className="alert alert-error">
                                    {error}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right: Output Content */}
                    <div style={{ background: 'rgba(30, 41, 59, 0.3)', borderRadius: '0.75rem', padding: '1rem', border: '1px solid #334155', minHeight: '400px', maxHeight: '600px', overflowY: 'auto' }}>
                        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: '#cbd5e1' }}>Decrypted Content</h2>

                        <AnimatePresence>
                            {decryptedFiles.length === 0 ? (
                                <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#475569', gap: '1rem', opacity: 0.5 }}>
                                    <Lock size={48} />
                                    <p>Vault Locked</p>
                                </div>
                            ) : (
                                <div>
                                    {decryptedFiles.map((file, idx) => (
                                        <motion.div
                                            key={idx}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: idx * 0.1 }}
                                            className="decrypted-item"
                                        >
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#22d3ee', fontWeight: 'bold', fontSize: '0.9rem', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>
                                                {file.type.startsWith('video') ? <FileVideo size={16} /> :
                                                    file.type.startsWith('image') ? <ImageIcon size={16} /> : <FileText size={16} />}
                                                {file.filename}
                                            </div>

                                            {file.type.startsWith('video') && (
                                                <video controls style={{ width: '100%', borderRadius: '0.25rem', background: 'black' }}>
                                                    <source src={file.blobUrl} type={file.type} />
                                                    Your browser does not support video tag.
                                                </video>
                                            )}

                                            {file.type.startsWith('image') && (
                                                <img src={file.blobUrl} alt="Decrypted" style={{ width: '100%', borderRadius: '0.25rem' }} />
                                            )}

                                            {file.type.startsWith('audio') && (
                                                <audio controls style={{ width: '100%' }}>
                                                    <source src={file.blobUrl} type={file.type} />
                                                    Your browser does not support audio tag.
                                                </audio>
                                            )}

                                            {file.type.startsWith('text') && (
                                                <pre style={{ fontSize: '0.75rem', fontFamily: 'monospace', background: 'rgba(0,0,0,0.5)', padding: '0.5rem', borderRadius: '0.25rem', whiteSpace: 'pre-wrap', color: '#4ade80', overflowX: 'auto' }}>
                                                    {decodeBase64UTF8(file.content)}
                                                </pre>
                                            )}

                                            {!file.type.startsWith('video') && !file.type.startsWith('image') && !file.type.startsWith('audio') && !file.type.startsWith('text') && (
                                                <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.5rem', textAlign: 'center' }}>
                                                    <FileText size={32} color="#94a3b8" style={{ marginBottom: '0.5rem' }} />
                                                    <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Secure Binary File ({file.type})</p>
                                                    <a
                                                        href={file.blobUrl}
                                                        download={file.filename}
                                                        className="btn-small"
                                                        style={{ display: 'inline-block', marginTop: '0.5rem', textDecoration: 'none' }}
                                                    >
                                                        Download Decrypted File
                                                    </a>
                                                </div>
                                            )}
                                        </motion.div>
                                    ))}
                                </div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

export default Receiver;
