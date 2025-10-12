import { useState, useRef, useCallback } from 'react';

/**
 * Custom hook for managing text input with mention functionality
 * Tracks cursor position and handles mention insertion
 */
export const useMentionInput = (initialValue = '') => {
  const [text, setText] = useState(initialValue);
  const [cursorPosition, setCursorPosition] = useState(null);
  const textareaRef = useRef(null); // Changed from inputRef to textareaRef to match usage

  // Update cursor position when user interacts with input
  const handleSelectionChange = useCallback(() => {
    if (textareaRef.current) {
      setCursorPosition(textareaRef.current.selectionStart);
    }
  }, []);

  // Handle text changes and track cursor
  const handleChange = useCallback((e) => {
    const newValue = e.target.value;
    console.log('⌨️ useMentionInput: Text changed', {
      value: newValue.substring(0, 50), // First 50 chars
      cursorPos: e.target.selectionStart
    });
    setText(newValue);
    // Use setTimeout to get cursor position after React updates
    setTimeout(() => {
      if (textareaRef.current) {
        const cursorPos = textareaRef.current.selectionStart;
        console.log('📍 useMentionInput: Cursor position updated to', cursorPos);
        setCursorPosition(cursorPos);
      }
    }, 0);
  }, []);

  // Handle mention selection and text replacement
  const handleMentionSelect = useCallback(({ user, startPos, endPos, replacement }) => {
    const newText = text.slice(0, startPos) + replacement + text.slice(endPos);
    setText(newText);

    // Set cursor position after the mention
    const newCursorPos = startPos + replacement.length;
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
        textareaRef.current.setSelectionRange(newCursorPos, newCursorPos);
        setCursorPosition(newCursorPos);
      }
    }, 0);
  }, [text]);

  // Handle key events for cursor tracking and navigation
  const handleKeyDown = useCallback((e) => {
    // Track cursor position on arrow keys and other navigation
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) {
      setTimeout(handleSelectionChange, 0);
    }
  }, [handleSelectionChange]);

  // Handle mouse clicks for cursor tracking
  const handleClick = useCallback(() => {
    handleSelectionChange();
  }, [handleSelectionChange]);

  return {
    text,
    setText,
    cursorPosition,
    textareaRef,
    handleChange,
    handleMentionSelect,
    handleKeyDown,
    handleClick,
    handleSelectionChange
  };
};

export default useMentionInput;
