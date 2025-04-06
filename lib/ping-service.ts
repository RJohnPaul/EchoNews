/**
 * Service to keep the Render backend alive by sending periodic requests
 */
class PingService {
  updateUrl(arg0: string) {
    throw new Error("Method not implemented.");
  }
  private interval: NodeJS.Timeout | null = null;
  private pingUrl: string;
  private intervalTime: number;
  
  constructor(url: string = '', intervalMinutes: number = 14) {
    this.pingUrl = url || process.env.NEXT_PUBLIC_API_URL || "https://newsai-swc7.onrender.com";
    this.intervalTime = intervalMinutes * 60 * 1000; // convert to milliseconds
  }
  
  start() {
    if (this.interval) return; // Already started
    
    // Initial ping
    this.ping();
    
    // Set up interval
    this.interval = setInterval(() => {
      this.ping();
    }, this.intervalTime);
    
    console.log(`Ping service started, pinging ${this.pingUrl} every ${this.intervalTime/60000} minutes`);
  }
  
  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
      console.log('Ping service stopped');
    }
  }
  
  private async ping() {
    try {
      const response = await fetch(`${this.pingUrl}/api/health`, {
        method: 'GET',
        cache: 'no-store',
      });
      console.log(`Pinged server, status: ${response.status}`);
    } catch (error) {
      console.error('Failed to ping server:', error);
    }
  }
}

// Singleton instance
const pingService = new PingService();
export default pingService;