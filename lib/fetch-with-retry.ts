/**
 * Utility function to fetch data with automatic retries and exponential backoff
 */
export async function fetchWithRetry(
    url: string, 
    options: RequestInit, 
    retries = 3, 
    backoff = 1500
  ): Promise<Response> {
    try {
      const response = await fetch(url, options);
      
      // If we get a timeout status and have retries left, try again
      if (response.status === 504 && retries > 0) {
        console.log(`Request timed out. Retrying in ${backoff}ms... (${retries} retries left)`);
        await new Promise(resolve => setTimeout(resolve, backoff));
        return fetchWithRetry(url, options, retries - 1, backoff * 1.5);
      }
      
      return response;
    } catch (err) {
      if (retries > 0) {
        console.log(`Fetch error. Retrying in ${backoff}ms... (${retries} retries left)`);
        await new Promise(resolve => setTimeout(resolve, backoff));
        return fetchWithRetry(url, options, retries - 1, backoff * 1.5);
      }
      throw err;
    }
  }