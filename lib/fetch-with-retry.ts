/**
 * Utility function to fetch data with automatic retries and exponential backoff
 */
export async function fetchWithRetry(
  url: string, 
  options: RequestInit, 
  retries = 3, 
  backoff = 1500,
  timeout = 90000 // Extended default timeout
): Promise<Response> {
  // Create AbortController for this request
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  // Add the signal to the options if not already present
  const fetchOptions = {
    ...options,
    signal: options.signal || controller.signal
  };
  
  try {
    const response = await fetch(url, fetchOptions);
    
    // Clear the timeout since the request completed
    clearTimeout(timeoutId);
    
    // If we get a timeout status and have retries left, try again
    if ((response.status === 504 || response.status === 503 || response.status === 502) && retries > 0) {
      console.log(`Server returned ${response.status}. Retrying in ${backoff}ms... (${retries} retries left)`);
      await new Promise(resolve => setTimeout(resolve, backoff));
      return fetchWithRetry(url, options, retries - 1, backoff * 1.5, timeout);
    }
    
    return response;
  } catch (err: any) {
    // Clear the timeout
    clearTimeout(timeoutId);
    
    if ((err.name === 'AbortError' || err.name === 'TimeoutError' || 
         err.message.includes('network') || err.message.includes('timeout')) && retries > 0) {
      console.log(`Fetch error: ${err.message}. Retrying in ${backoff}ms... (${retries} retries left)`);
      await new Promise(resolve => setTimeout(resolve, backoff));
      return fetchWithRetry(url, options, retries - 1, backoff * 1.5, timeout);
    }
    throw err;
  }
}