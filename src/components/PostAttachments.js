import React from 'react';
import styles from './PostAttachments.module.css';

const PostAttachments = ({ attachments }) => {
    if (!attachments || attachments.length === 0) return null;

    if (attachments.length === 1) {
        const attachment = attachments[0];
        return (
            <div className={styles.attachments}>
                <div className={styles.singleAttachment}>
                    {attachment.type === 'image' ? (
                        <img
                            src={attachment.url}
                            alt={attachment.alt || 'Pièce jointe'}
                            className={styles.attachmentImage}
                        />
                    ) : (
                        <video
                            src={attachment.url}
                            className={styles.attachmentVideo}
                            controls
                        />
                    )}
                </div>
            </div>
        );
    }

    const getGridClass = (count) => {
        if (count === 2) return styles.twoItems;
        if (count === 3) return styles.threeItems;
        return styles.fourPlusItems;
    };

    return (
        <div className={styles.attachments}>
            <div className={`${styles.multipleAttachments} ${getGridClass(attachments.length)}`}>
                {attachments.slice(0, 4).map((attachment, index) => (
                    <div key={attachment.id} className={styles.attachmentItem}>
                        {attachment.type === 'image' ? (
                            <img
                                src={attachment.url}
                                alt={attachment.alt || `Pièce jointe ${index + 1}`}
                            />
                        ) : (
                            <video src={attachment.url} />
                        )}
                        {index === 3 && attachments.length > 4 && (
                            <div className={styles.moreOverlay}>
                                +{attachments.length - 4}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PostAttachments;