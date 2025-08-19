/**
 * BGM (Background Music) Service
 * Provides global background music functionality with random selection, volume control, and toggle features
 */

class BGMService {
    constructor() {
        this.audio = null;
        this.isPlaying = false;
        this.volume = 0.5; // Default volume (0-1)
        this.bgmFolder = '/static/bgm/';
        this.currentTrack = null;
        this.tracks = [];
        
        this.init();
    }

    async init() {
        try {
            await this.loadTracks();
            console.log('BGM Service initialized with tracks:', this.tracks);
        } catch (error) {
            console.error('Failed to initialize BGM Service:', error);
        }
    }

    async loadTracks() {
        try {
            // Get list of audio files from the bgm folder
            const response = await fetch('/api/bgm-tracks');
            if (response.ok) {
                this.tracks = await response.json();
            } else {
                // Fallback: use known tracks if API fails
                this.tracks = ['bgm01.aac']; // Add more as needed
            }
        } catch (error) {
            console.warn('Could not load BGM tracks from API, using fallback:', error);
            this.tracks = ['bgm01.aac'];
        }
    }

    /**
     * Play a random BGM track
     */
    async playRandom() {
        if (this.tracks.length === 0) {
            console.warn('No BGM tracks available');
            return;
        }

        const randomIndex = Math.floor(Math.random() * this.tracks.length);
        const track = this.tracks[randomIndex];
        
        await this.playTrack(track);
    }

    /**
     * Play a specific track
     * @param {string} trackName - Name of the track to play
     */
    async playTrack(trackName) {
        try {
            if (this.audio) {
                this.audio.pause();
                this.audio.currentTime = 0;
            }

            this.audio = new Audio(`${this.bgmFolder}${trackName}`);
            this.audio.volume = this.volume;
            this.audio.loop = true;
            
            await this.audio.play();
            this.isPlaying = true;
            this.currentTrack = trackName;
            
            console.log(`Playing BGM: ${trackName}`);
        } catch (error) {
            console.error('Error playing BGM:', error);
            this.isPlaying = false;
        }
    }

    /**
     * Pause the current BGM
     */
    pause() {
        if (this.audio && this.isPlaying) {
            this.audio.pause();
            this.isPlaying = false;
            console.log('BGM paused');
        }
    }

    /**
     * Resume the current BGM
     */
    resume() {
        if (this.audio && !this.isPlaying) {
            this.audio.play().then(() => {
                this.isPlaying = true;
                console.log('BGM resumed');
            }).catch(error => {
                console.error('Error resuming BGM:', error);
            });
        }
    }

    /**
     * Stop the current BGM
     */
    stop() {
        if (this.audio) {
            this.audio.pause();
            this.audio.currentTime = 0;
            this.isPlaying = false;
            console.log('BGM stopped');
        }
    }

    /**
     * Toggle BGM on/off
     * @returns {boolean} - New playing state
     */
    toggle() {
        if (this.isPlaying) {
            this.pause();
        } else {
            if (this.currentTrack) {
                this.resume();
            } else {
                this.playRandom();
            }
        }
        return this.isPlaying;
    }

    /**
     * Set BGM volume
     * @param {number} volume - Volume level (0-1)
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        if (this.audio) {
            this.audio.volume = this.volume;
        }
        console.log(`BGM volume set to: ${Math.round(this.volume * 100)}%`);
    }

    /**
     * Get current volume
     * @returns {number} - Current volume level (0-1)
     */
    getVolume() {
        return this.volume;
    }

    /**
     * Get current playing state
     * @returns {boolean} - Whether BGM is currently playing
     */
    getPlayingState() {
        return this.isPlaying;
    }

    /**
     * Get current track name
     * @returns {string|null} - Name of current track or null if none
     */
    getCurrentTrack() {
        return this.currentTrack;
    }

    /**
     * Get available tracks
     * @returns {Array<string>} - List of available BGM tracks
     */
    getAvailableTracks() {
        return [...this.tracks];
    }

    /**
     * Refresh the track list
     */
    async refreshTracks() {
        await this.loadTracks();
    }
}

// Create global BGM service instance
window.bgmService = new BGMService();

// Auto-play BGM when page loads (respect browser autoplay policies)
document.addEventListener('DOMContentLoaded', () => {
    // Attempt to play BGM after user interaction
    const playBGMOnInteraction = () => {
        if (!window.bgmService.isPlaying && window.bgmService.tracks.length > 0) {
            window.bgmService.playRandom();
        }
        // Remove listeners after first interaction
        document.removeEventListener('click', playBGMOnInteraction);
        document.removeEventListener('keydown', playBGMOnInteraction);
        document.removeEventListener('touchstart', playBGMOnInteraction);
    };

    document.addEventListener('click', playBGMOnInteraction);
    document.removeEventListener('keydown', playBGMOnInteraction);
    document.removeEventListener('touchstart', playBGMOnInteraction);
});
