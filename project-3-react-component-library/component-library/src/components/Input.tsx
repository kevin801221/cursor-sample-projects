import React, { forwardRef, useId } from 'react';
import './components.css';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  errorMessage?: string;
  isError?: boolean;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      errorMessage,
      isError = false,
      id,
      className = '',
      disabled,
      startIcon,
      endIcon,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = id || generatedId;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;
    const hasError = isError || Boolean(errorMessage);

    const inputClasses = [
      'input-field',
      hasError ? 'input-field--error' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className="input-group">
        {label && (
          <label htmlFor={inputId} className="input-label">
            {label}
          </label>
        )}
        <div className="input-wrapper">
          {startIcon && <span style={{ position: 'absolute', left: 12 }}>{startIcon}</span>}
          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            className={inputClasses}
            style={{
              paddingLeft: startIcon ? 36 : undefined,
              paddingRight: endIcon ? 36 : undefined,
            }}
            aria-invalid={hasError}
            aria-describedby={
              hasError ? errorId : helperText ? helperId : undefined
            }
            {...props}
          />
          {endIcon && <span style={{ position: 'absolute', right: 12 }}>{endIcon}</span>}
        </div>
        {hasError && errorMessage && (
          <p id={errorId} className="input-msg input-msg--error" role="alert">
            {errorMessage}
          </p>
        )}
        {!hasError && helperText && (
          <p id={helperId} className="input-msg">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
