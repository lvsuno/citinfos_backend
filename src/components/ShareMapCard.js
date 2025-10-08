import React, { useState } from 'react';
import {
    Share as ShareIcon,
    ContentCopy as CopyIcon,
    QrCode2 as QrCodeIcon,
    Facebook as FacebookIcon,
    Twitter as TwitterIcon,
    LinkedIn as LinkedInIcon,
    WhatsApp as WhatsAppIcon,
    Check as CheckIcon,
} from '@mui/icons-material';
import styles from './ShareMapCard.module.css';

const ShareMapCard = ({ selectedDivision, selectedCountry }) => {
    const [copied, setCopied] = useState(false);
    const [showQR, setShowQR] = useState(false);
    const [showSocialMenu, setShowSocialMenu] = useState(false);
    const qrCodeRef = React.useRef(null);

    // Generate QR code when shown
    React.useEffect(() => {
        if (showQR && qrCodeRef.current) {
            console.log('📱 Generating QR code for URL:', getShareUrl());

            import('qrcode').then(QRCode => {
                QRCode.default.toCanvas(
                    qrCodeRef.current,
                    getShareUrl(),
                    {
                        width: 200,
                        margin: 2,
                        color: {
                            dark: '#0e7490',
                            light: '#ffffff'
                        }
                    },
                    (error) => {
                        if (error) {
                            console.error('❌ QR Code generation error:', error);
                        } else {
                            console.log('✅ QR Code generated successfully');
                        }
                    }
                );
            }).catch(err => {
                console.error('❌ Failed to load qrcode library:', err);
            });
        }
    }, [showQR]);

    // Generate the shareable URL
    const getShareUrl = () => {
        if (!selectedDivision?.id) {
            return window.location.origin + '/carte';
        }
        return `${window.location.origin}/carte?division=${selectedDivision.id}`;
    };

    const getShareTitle = () => {
        if (!selectedDivision?.name) {
            return 'Carte Interactive - Citinfos';
        }
        return `${selectedDivision.name} sur Citinfos`;
    };

    const getShareText = () => {
        if (!selectedDivision?.name) {
            return 'Explorez les divisions administratives sur la carte interactive';
        }
        return `Découvrez ${selectedDivision.name} sur la carte interactive de Citinfos`;
    };

    const shareUrl = getShareUrl();
    const shareTitle = getShareTitle();
    const shareText = getShareText();

    // Copy link to clipboard
    const handleCopyLink = async () => {
        try {
            await navigator.clipboard.writeText(shareUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error('Failed to copy:', error);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = shareUrl;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Share to social networks
    const handleShareFacebook = () => {
        const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
        window.open(url, '_blank', 'width=600,height=400');
    };

    const handleShareTwitter = () => {
        const url = `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(shareText)}`;
        window.open(url, '_blank', 'width=600,height=400');
    };

    const handleShareLinkedIn = () => {
        const url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
        window.open(url, '_blank', 'width=600,height=400');
    };

    const handleShareWhatsApp = () => {
        const url = `https://wa.me/?text=${encodeURIComponent(shareText + ' ' + shareUrl)}`;
        window.open(url, '_blank', 'width=600,height=400');
    };

    // Native Web Share API (for mobile devices)
    const handleNativeShare = async () => {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: shareTitle,
                    text: shareText,
                    url: shareUrl,
                });
            } catch (error) {
                console.error('Error sharing:', error);
            }
        }
    };

    return (
        <div className={styles.shareCard}>
            <div className={styles.cardHeader}>
                <ShareIcon className={styles.cardIcon} />
                <span className={styles.cardTitle}>Partager cette carte</span>
            </div>

            <div className={styles.shareContent}>
                {/* Division info */}
                {selectedDivision && (
                    <div className={styles.divisionInfo}>
                        <p className={styles.divisionName}>{selectedDivision.name}</p>
                        {selectedCountry && (
                            <p className={styles.divisionCountry}>
                                {selectedCountry.name}
                            </p>
                        )}
                    </div>
                )}

                {/* Compact sharing actions */}
                <div className={styles.compactActions}>
                    {/* Copy link button */}
                    <button
                        className={`${styles.actionButton} ${copied ? styles.copied : ''}`}
                        onClick={handleCopyLink}
                        title={copied ? "Lien copié!" : "Copier le lien"}
                    >
                        {copied ? <CheckIcon /> : <CopyIcon />}
                    </button>

                    {/* Social share button with arc menu */}
                    <div className={styles.socialShareWrapper}>
                        <button
                            className={`${styles.actionButton} ${showSocialMenu ? styles.active : ''}`}
                            onClick={() => setShowSocialMenu(!showSocialMenu)}
                            title="Partager sur les réseaux sociaux"
                        >
                            <ShareIcon />
                        </button>

                        {/* Arc menu */}
                        {showSocialMenu && (
                            <div className={styles.socialArcMenu}>
                                <button
                                    className={`${styles.arcButton} ${styles.facebook}`}
                                    onClick={() => {
                                        handleShareFacebook();
                                        setShowSocialMenu(false);
                                    }}
                                    title="Facebook"
                                >
                                    <FacebookIcon />
                                </button>
                                <button
                                    className={`${styles.arcButton} ${styles.twitter}`}
                                    onClick={() => {
                                        handleShareTwitter();
                                        setShowSocialMenu(false);
                                    }}
                                    title="Twitter"
                                >
                                    <TwitterIcon />
                                </button>
                                <button
                                    className={`${styles.arcButton} ${styles.linkedin}`}
                                    onClick={() => {
                                        handleShareLinkedIn();
                                        setShowSocialMenu(false);
                                    }}
                                    title="LinkedIn"
                                >
                                    <LinkedInIcon />
                                </button>
                                <button
                                    className={`${styles.arcButton} ${styles.whatsapp}`}
                                    onClick={() => {
                                        handleShareWhatsApp();
                                        setShowSocialMenu(false);
                                    }}
                                    title="WhatsApp"
                                >
                                    <WhatsAppIcon />
                                </button>
                            </div>
                        )}
                    </div>

                    {/* QR Code button */}
                    <button
                        className={`${styles.actionButton} ${showQR ? styles.active : ''}`}
                        onClick={() => setShowQR(!showQR)}
                        title={showQR ? "Masquer le QR Code" : "Afficher le QR Code"}
                    >
                        <QrCodeIcon />
                    </button>

                    {/* QR Code tooltip/popover */}
                    {showQR && (
                        <>
                            <div
                                className={styles.qrOverlay}
                                onClick={() => setShowQR(false)}
                            />
                            <div className={styles.qrTooltip}>
                                <button
                                    className={styles.closeQR}
                                    onClick={() => setShowQR(false)}
                                    aria-label="Fermer"
                                >
                                    ×
                                </button>
                                <canvas
                                    ref={qrCodeRef}
                                    className={styles.qrCode}
                                />
                                <p className={styles.qrCodeLabel}>
                                    Scannez pour accéder à la carte
                                </p>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ShareMapCard;
