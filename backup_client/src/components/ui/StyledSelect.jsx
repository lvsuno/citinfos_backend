import { useState, useRef, useEffect } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

const StyledSelect = ({
  value,
  onChange,
  options = [],
  placeholder = "Select option",
  className = "",
  size = "normal", // "small" | "normal" | "large"
  disabled = false,
  error = false,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const selectRef = useRef(null);
  const optionsRef = useRef([]);

  // Size classes
  const sizeClasses = {
    small: {
      button: "px-2 py-1 text-sm min-h-[32px]",
      option: "px-2 py-1.5 text-sm",
      icon: "h-3 w-3"
    },
    normal: {
      button: "px-3 py-2 text-sm min-h-[36px]",
      option: "px-3 py-2 text-sm",
      icon: "h-4 w-4"
    },
    large: {
      button: "px-4 py-3 text-base min-h-[44px]",
      option: "px-4 py-3 text-base",
      icon: "h-5 w-5"
    }
  };

  const currentSizeClasses = sizeClasses[size] || sizeClasses.normal;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        setIsOpen(true);
        setHighlightedIndex(options.findIndex(opt => opt.value === value));
      }
      return;
    }

    switch (e.key) {
      case 'Escape':
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => prev < options.length - 1 ? prev + 1 : 0);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : options.length - 1);
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0) {
          handleSelect(options[highlightedIndex]);
        }
        break;
      case 'Tab':
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
    }
  };

  // Scroll highlighted option into view
  useEffect(() => {
    if (highlightedIndex >= 0 && optionsRef.current[highlightedIndex]) {
      optionsRef.current[highlightedIndex].scrollIntoView({
        block: 'nearest',
        behavior: 'smooth'
      });
    }
  }, [highlightedIndex]);

  const handleSelect = (option) => {
    onChange(option.value);
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const selectedOption = options.find(opt => opt.value === value);

  const baseClasses = `
    relative w-full bg-white border rounded-lg
    focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500
    transition-all duration-200 ease-in-out
    cursor-pointer select-none
    flex items-center justify-between
  `;

  const stateClasses = `
    ${error
      ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
      : 'border-gray-300 hover:border-gray-400'
    }
    ${disabled
      ? 'bg-gray-50 text-gray-400 cursor-not-allowed'
      : 'hover:bg-gray-50'
    }
    ${isOpen ? 'ring-2 ring-indigo-500 border-indigo-500' : ''}
  `;

  return (
    <div ref={selectRef} className={`relative ${className}`}>
      {/* Select Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={`${baseClasses} ${stateClasses} ${currentSizeClasses.button}`}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        {...props}
      >
        <span className={`block truncate ${selectedOption ? 'text-gray-900' : 'text-gray-500'}`}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>

        {isOpen ? (
          <ChevronUpIcon className={`${currentSizeClasses.icon} text-gray-400 flex-shrink-0 ml-2`} />
        ) : (
          <ChevronDownIcon className={`${currentSizeClasses.icon} text-gray-400 flex-shrink-0 ml-2`} />
        )}
      </button>

      {/* Dropdown Options */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
          {options.map((option, index) => (
            <button
              key={option.value}
              ref={el => optionsRef.current[index] = el}
              type="button"
              onClick={() => handleSelect(option)}
              className={`
                ${currentSizeClasses.option}
                w-full text-left hover:bg-indigo-50 hover:text-indigo-900
                focus:outline-none focus:bg-indigo-50 focus:text-indigo-900
                transition-colors duration-150 ease-in-out
                ${index === highlightedIndex ? 'bg-indigo-50 text-indigo-900' : 'text-gray-900'}
                ${option.value === value ? 'bg-indigo-100 text-indigo-900 font-medium' : ''}
                ${index === 0 ? 'rounded-t-lg' : ''}
                ${index === options.length - 1 ? 'rounded-b-lg' : ''}
              `}
              role="option"
              aria-selected={option.value === value}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default StyledSelect;
