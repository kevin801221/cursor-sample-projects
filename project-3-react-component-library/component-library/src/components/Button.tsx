import React, { forwardRef } from 'react';
import './components.css';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  isFullWidth?: boolean;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      isFullWidth = false,
      disabled = false,
      startIcon,
      endIcon,
      className = '',
      type = 'button',
      ...props
    },
    ref
  ) => {
    const classNames = [
      'btn',
      `btn--${variant}`,
      `btn--${size}`,
      isFullWidth ? 'btn--full' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        type={type}
        className={classNames}
        disabled={disabled || isLoading}
        aria-busy={isLoading}
        {...props}
      >
        {isLoading && <span className="btn-spinner" aria-hidden="true" />}
        {!isLoading && startIcon && <span className="btn-icon">{startIcon}</span>}
        <span>{children}</span>
        {!isLoading && endIcon && <span className="btn-icon">{endIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
