import React from 'react';
import styles from './PostContent.module.css';

const PostContent = ({ content }) => {
    const formatContent = (text) => {
        return text.split('\n').map((line, index) => (
            <React.Fragment key={index}>
                {line}
                {index < text.split('\n').length - 1 && <br />}
            </React.Fragment>
        ));
    };

    return (
        <div className={styles.postContent}>
            <p>{formatContent(content)}</p>
        </div>
    );
};

export default PostContent;