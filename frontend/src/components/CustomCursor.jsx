import { useEffect, useRef, useState } from 'react';
import { motion, useSpring, useMotionValue } from 'framer-motion';

/**
 * Custom cursor with glowing dot + trailing ring.
 * Only renders on devices with a fine pointer (mouse).
 */
const CustomCursor = () => {
    const [visible, setVisible] = useState(false);
    const [hoveringInteractive, setHoveringInteractive] = useState(false);
    const [clicking, setClicking] = useState(false);

    const cursorX = useMotionValue(-100);
    const cursorY = useMotionValue(-100);

    // Ring follows with a spring delay
    const ringX = useSpring(cursorX, { stiffness: 150, damping: 20, mass: 0.5 });
    const ringY = useSpring(cursorY, { stiffness: 150, damping: 20, mass: 0.5 });

    const rafRef = useRef(null);

    useEffect(() => {
        // Only show on non-touch devices
        const isPointerFine = window.matchMedia('(pointer: fine)').matches;
        if (!isPointerFine) return;

        const onMouseMove = (e) => {
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
            rafRef.current = requestAnimationFrame(() => {
                cursorX.set(e.clientX);
                cursorY.set(e.clientY);
            });
            if (!visible) setVisible(true);
        };

        const onMouseDown = () => setClicking(true);
        const onMouseUp = () => setClicking(false);

        const onMouseEnter = () => setVisible(true);
        const onMouseLeave = () => setVisible(false);

        // Detect hovering over interactive elements
        const onMouseOver = (e) => {
            const target = e.target.closest(
                'a, button, [role="button"], input, textarea, select, label, .cursor-pointer'
            );
            setHoveringInteractive(!!target);
        };

        document.addEventListener('mousemove', onMouseMove, { passive: true });
        document.addEventListener('mousedown', onMouseDown);
        document.addEventListener('mouseup', onMouseUp);
        document.addEventListener('mouseenter', onMouseEnter);
        document.addEventListener('mouseleave', onMouseLeave);
        document.addEventListener('mouseover', onMouseOver, { passive: true });

        // Add class to hide default cursor
        document.documentElement.classList.add('custom-cursor-active');

        return () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mousedown', onMouseDown);
            document.removeEventListener('mouseup', onMouseUp);
            document.removeEventListener('mouseenter', onMouseEnter);
            document.removeEventListener('mouseleave', onMouseLeave);
            document.removeEventListener('mouseover', onMouseOver);
            document.documentElement.classList.remove('custom-cursor-active');
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
        };
    }, [cursorX, cursorY, visible]);

    if (!visible) return null;

    const dotSize = clicking ? 6 : hoveringInteractive ? 10 : 8;
    const ringSize = hoveringInteractive ? 48 : 36;

    return (
        <>
            {/* Inner glowing dot */}
            <motion.div
                className="custom-cursor-dot"
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    x: cursorX,
                    y: cursorY,
                    width: dotSize,
                    height: dotSize,
                    borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(129,140,248,1) 0%, rgba(99,102,241,0.8) 60%, rgba(99,102,241,0) 100%)',
                    boxShadow: '0 0 12px 4px rgba(99,102,241,0.5), 0 0 24px 8px rgba(99,102,241,0.2)',
                    pointerEvents: 'none',
                    zIndex: 99999,
                    translateX: '-50%',
                    translateY: '-50%',
                    transition: 'width 0.15s ease, height 0.15s ease',
                }}
            />
            {/* Outer trailing ring */}
            <motion.div
                className="custom-cursor-ring"
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    x: ringX,
                    y: ringY,
                    width: ringSize,
                    height: ringSize,
                    borderRadius: '50%',
                    border: `1.5px solid rgba(129, 140, 248, ${hoveringInteractive ? 0.6 : 0.3})`,
                    background: hoveringInteractive
                        ? 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)'
                        : 'transparent',
                    pointerEvents: 'none',
                    zIndex: 99998,
                    translateX: '-50%',
                    translateY: '-50%',
                    transition: 'width 0.2s ease, height 0.2s ease, border-color 0.2s ease, background 0.2s ease',
                }}
            />
        </>
    );
};

export default CustomCursor;
