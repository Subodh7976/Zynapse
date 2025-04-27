import { useState, useEffect, useRef, useCallback } from 'react';

const DEFAULT_TYPE_SPEED_MS = 10;

export function useTypewriter(
    targetText: string,
    isStreaming: boolean = false,
    speed: number = DEFAULT_TYPE_SPEED_MS
): string {
    const [displayedText, setDisplayedText] = useState('');
    const currentIndexRef = useRef(0);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    const clearTypeInterval = useCallback(() => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    }, []);

    useEffect(() => {
        const typeCharacter = () => {
            const currentIdx = currentIndexRef.current;

            if (currentIdx >= targetText.length) {
                clearTypeInterval(); 
                return;
            }

            setDisplayedText(targetText.substring(0, currentIdx + 1));
            currentIndexRef.current = currentIdx + 1;
        };


        if (!isStreaming) {
            clearTypeInterval();
            setDisplayedText(targetText);
            currentIndexRef.current = targetText.length;
        } else {
            if (displayedText === targetText) {
                clearTypeInterval();
                currentIndexRef.current = targetText.length;
                return;
            }

             if (targetText.length < currentIndexRef.current) {
                 clearTypeInterval();
                 setDisplayedText(targetText);
                 currentIndexRef.current = targetText.length;
             }


            if (!intervalRef.current && currentIndexRef.current < targetText.length) {
                 setDisplayedText(targetText.substring(0, currentIndexRef.current));
                 intervalRef.current = setInterval(typeCharacter, speed);
            }
        }

        return () => {
            clearTypeInterval();
        };

    }, [targetText, isStreaming, speed, clearTypeInterval, displayedText]); // Add displayedText dependency to handle reset case

    useEffect(() => {
         if (!targetText && displayedText) {
             currentIndexRef.current = 0;
             setDisplayedText('');
         }
    }, [targetText, displayedText]);


    return displayedText;
}