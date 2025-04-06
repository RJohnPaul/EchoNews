/* eslint-disable @next/next/no-img-element */
/* eslint-disable @next/next/no-img-element */
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { 
  Loader2, 
  Search, 
  Globe, 
  Clock, 
  ArrowRight, 
  Newspaper, 
  ChevronLeft, 
  ChevronRight,
  RefreshCw,
  ExternalLink,
  Star,
  Filter,
  LogOut,
  AlertTriangle
} from "lucide-react";
import { 
  Sheet, 
  SheetContent, 
  SheetDescription, 
  SheetHeader, 
  SheetTitle, 
  SheetTrigger,
  SheetFooter,
  SheetClose
} from "@/components/ui/sheet";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { fetchWithRetry } from "@/lib/fetch-with-retry";

// Define form schema with Zod
const formSchema = z.object({
  query: z.string().min(2, {
    message: "Query must be at least 2 characters",
  }),
  language: z.string({
    required_error: "Please select a language",
  }),
  preferred_sources: z.array(z.string()).optional(),
});

// Define the types
interface NewsSource {
  name: string;
  url?: string;
  id?: string;
  image?: string;
}

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  source: NewsSource;
  published_date: string;
  link: string;
  relevance?: number;
  image_url?: string;
}

interface NewsResponse {
  articles: NewsArticle[];
  message: string;
  total_found: number;
  total_pages: number;
  current_page: number;
  available_sources: string[];
}

// Get relative time format
function getRelativeTime(dateString: string) {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return 'just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} min${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 604800) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  } catch (e) {
    return "unknown date";
  }
}

// Server warm-up warning component
function ServerWarmupWarning({ isVisible, onRetry }: { isVisible: boolean, onRetry: () => void }) {
  if (!isVisible) return null;
  
  return (
    <Alert className="mb-6 border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-800">
      <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
      <AlertTitle className="text-yellow-800 dark:text-yellow-400">Server Warming Up</AlertTitle>
      <AlertDescription className="text-yellow-700 dark:text-yellow-300 flex flex-col space-y-3">
        <p>Our backend server is starting up after a period of inactivity. This may take up to 30 seconds.</p>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={onRetry}
          className="w-fit text-yellow-700 border-yellow-300 hover:bg-yellow-100 dark:text-yellow-400 dark:border-yellow-800 dark:hover:bg-yellow-900/30"
        >
          <RefreshCw className="h-3 w-3 mr-1" />
          Try Again
        </Button>
      </AlertDescription>
    </Alert>
  );
}

// Relevance indicator component
function RelevanceIndicator({ score }: { score?: number }) {
  if (!score) return null;
  
  const getRelevanceColor = (score: number) => {
    if (score > 0.8) return "bg-green-500";
    if (score > 0.6) return "bg-green-400";
    if (score > 0.4) return "bg-yellow-400";
    if (score > 0.2) return "bg-orange-400";
    return "bg-red-400";
  };
  
  const percent = Math.round(score * 100);
  
  return (
    <div className="flex items-center gap-1 text-xs text-muted-foreground">
      <div className="flex h-2 w-20 overflow-hidden rounded-full bg-muted">
        <div 
          className={`${getRelevanceColor(score)}`} 
          style={{ width: `${percent}%` }} 
        />
      </div>
      <Star className="h-3 w-3" />
      <span>{percent}%</span>
    </div>
  );
}

// Article card component
function ArticleCard({ article }: { article: NewsArticle }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-300">
        <div className="md:flex">
          {article.image_url && (
            <div className="md:w-1/3 h-48 md:h-auto overflow-hidden bg-slate-100">
              <img 
                src={article.image_url} 
                alt={article.title}
                className="w-full h-full object-cover" 
                onError={(e) => {
                  // Fallback if image fails to load
                  const target = e.target as HTMLImageElement;
                  target.src = "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg";
                }}
              />
            </div>
          )}
          <div className={`${article.image_url ? 'md:w-2/3' : 'w-full'}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="text-xs font-normal">
                  {article.source.name}
                </Badge>
                <RelevanceIndicator score={article.relevance} />
              </div>
              <CardTitle className="text-xl mt-2 line-clamp-2">{article.title}</CardTitle>
              <div className="flex items-center text-xs text-muted-foreground">
                <Clock className="h-3 w-3 mr-1" />
                {getRelativeTime(article.published_date)}
              </div>
            </CardHeader>
            <CardContent className="pb-2">
              <p className="text-sm text-muted-foreground line-clamp-3">{article.summary}</p>
            </CardContent>
            <CardFooter className="pt-2 flex justify-between">
              <Button variant="outline" size="sm" asChild>
                <a href={article.link} target="_blank" rel="noopener noreferrer" className="flex items-center">
                  Read more <ExternalLink className="h-3 w-3 ml-1" />
                </a>
              </Button>
            </CardFooter>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

// Source button component
function SourceButton({ 
  source, 
  selected, 
  onClick 
}: { 
  source: string; 
  selected: boolean; 
  onClick: () => void;
}) {
  return (
    <Button
      type="button"
      variant={selected ? "default" : "outline"}
      size="sm"
      onClick={onClick}
      className="mb-2 mr-2"
    >
      <Newspaper className="h-3 w-3 mr-1" />
      {source}
    </Button>
  );
}

// Pagination component
function Pagination({
  currentPage,
  totalPages,
  onPageChange
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const visiblePages = 5; // Number of page buttons to show
  
  // Calculate range of visible page numbers
  let startPage = Math.max(1, currentPage - Math.floor(visiblePages / 2));
  const endPage = Math.min(totalPages, startPage + visiblePages - 1);
  
  if (endPage - startPage + 1 < visiblePages) {
    startPage = Math.max(1, endPage - visiblePages + 1);
  }
  
  // Generate array of page numbers to display
  const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);
  
  if (totalPages <= 1) return null;
  
  return (
    <div className="flex items-center justify-center mt-6">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      
      {startPage > 1 && (
        <>
          <Button variant="outline" size="sm" onClick={() => onPageChange(1)}>1</Button>
          {startPage > 2 && <span className="mx-1">...</span>}
        </>
      )}
      
      {pages.map(page => (
        <Button
          key={page}
          variant={page === currentPage ? "default" : "outline"}
          size="sm"
          className="mx-1"
          onClick={() => onPageChange(page)}
        >
          {page}
        </Button>
      ))}
      
      {endPage < totalPages && (
        <>
          {endPage < totalPages - 1 && <span className="mx-1">...</span>}
          <Button variant="outline" size="sm" onClick={() => onPageChange(totalPages)}>
            {totalPages}
          </Button>
        </>
      )}
      
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}

export default function NewsQueryPage() {
  const router = useRouter(); // Add router for authentication navigation
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isServerWarming, setIsServerWarming] = useState<boolean>(false);
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [totalFound, setTotalFound] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [pageSize] = useState<number>(10);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState<boolean>(true);
  
  // Server wake-up ping on initial load
  useEffect(() => {
    const pingServer = async () => {
      try {
        // Send a lightweight request to wake up the server
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/api/health`, {
          method: "GET",
          cache: "no-store",
        });
        console.log("Backend server ping successful");
      } catch (err) {
        console.log("Backend server ping failed, may need warm-up time");
      }
    };
    
    pingServer();
    
    // Set up periodic ping to keep server warm (every 14 minutes)
    const pingInterval = setInterval(pingServer, 14 * 60 * 1000);
    
    return () => clearInterval(pingInterval);
  }, []);
  
  // Check if user is logged in
  useEffect(() => {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn) {
      router.push('/login');
    } else {
      // Also set a cookie for middleware authentication
      document.cookie = `isLoggedIn=true; path=/; max-age=86400`; // 24 hours
    }
  }, [router]);

  // Logout function
  const handleLogout = () => {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('loginTime');
    
    // Clear the cookie as well
    document.cookie = 'isLoggedIn=; path=/; max-age=0';
    
    router.push('/login');
  };
  
  // Initialize form with react-hook-form and zod validation
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      query: "",
      language: "en",
      preferred_sources: [],
    },
  });

  // Watch for language changes to fetch available sources
  const selectedLanguage = form.watch("language");
  
  // Fetch available sources when language changes
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const response = await fetchWithRetry(`/api/news/sources/${selectedLanguage}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }, 2);
        
        if (response.ok) {
          const data = await response.json();
          const sourceNames = data.sources.map((s: any) => s.name);
          setAvailableSources(sourceNames);
          
          // Reset selected sources when language changes
          setSelectedSources([]);
          form.setValue("preferred_sources", []);
          
          // Server responded successfully, so it's not warming up
          setIsServerWarming(false);
        } else if (response.status === 504) {
          // Server is probably warming up
          setIsServerWarming(true);
          console.warn("Server timeout when fetching sources, may be warming up");
        } else {
          console.error("Failed to fetch sources:", response.status);
        }
      } catch (err) {
        console.error("Error fetching sources:", err);
        // Check if it's likely a timeout issue
        if (err instanceof Error && 
            (err.message.includes("timeout") || err.message.includes("network") || err.name === "AbortError")) {
          setIsServerWarming(true);
        }
      }
    };

    if (selectedLanguage) {
      fetchSources();
    }
  }, [selectedLanguage, form]);

  // Handle source selection
  const toggleSource = (source: string) => {
    const newSources = selectedSources.includes(source)
      ? selectedSources.filter(s => s !== source)
      : [...selectedSources, source];
    
    setSelectedSources(newSources);
    form.setValue("preferred_sources", newSources);
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    fetchNews(form.getValues(), newPage);
    
    if (autoScrollEnabled) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Fetch news from API with retry mechanism
  const fetchNews = async (values: z.infer<typeof formSchema>, page = 1) => {
    setLoading(true);
    setError(null);
    
    try {
      // Use fetchWithRetry to handle timeouts and retries
      const response = await fetchWithRetry("/api/news", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: values.query,
          language: values.language,
          page: page,
          page_size: pageSize,
          preferred_sources: values.preferred_sources || [],
        }),
      }, 3); // Try up to 3 times with backoff

      if (response.status === 504) {
        setIsServerWarming(true);
        setError("The server is taking longer than expected to respond. It might be starting up after inactivity.");
        setLoading(false);
        return;
      }

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data: NewsResponse = await response.json();
      
      // Server responded successfully, so it's not warming up anymore
      setIsServerWarming(false);
      
      // Update state with API response
      setArticles(data.articles);
      setMessage(data.message);
      setTotalFound(data.total_found);
      setTotalPages(data.total_pages);
      setCurrentPage(data.current_page);
      
      if (data.available_sources?.length) {
        setAvailableSources(data.available_sources);
      }
    } catch (err) {
      console.error("Error fetching news:", err);
      
      // Check if it's likely a timeout issue
      if (err instanceof Error && 
          (err.message.includes("timeout") || err.message.includes("network") || err.name === "AbortError")) {
        setIsServerWarming(true);
        setError("Connection to the server timed out. The server might be starting up after inactivity.");
      } else {
        setError(err instanceof Error ? err.message : "An unknown error occurred");
      }
      
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle form submission
  async function onSubmit(values: z.infer<typeof formSchema>) {
    // Reset to first page on new search
    setCurrentPage(1);
    setArticles([]);
    setMessage("");
    setTotalFound(0);
    
    await fetchNews(values, 1);
  }

  // Retry handler for server warming up state
  const handleRetry = () => {
    const values = form.getValues();
    fetchNews(values, currentPage);
  };

  const languageOptions = [
    { value: "en", label: "English", icon: "🇬🇧" },
    { value: "hi", label: "Hindi", icon: "🇮🇳" },
    { value: "ta", label: "Tamil", icon: "🇮🇳" },
    { value: "te", label: "Telugu", icon: "🇮🇳" },
    { value: "mr", label: "Marathi", icon: "🇮🇳" },
    { value: "gu", label: "Gujarati", icon: "🇮🇳" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      {/* Hero section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-12 px-4">
        <div className="container mx-auto max-w-5xl">
          {/* Add logout button */}
          <div className="flex justify-end mb-4">
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="text-white border-white/30 hover:bg-white/10"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-center">
            Multilingual News Search
          </h1>
          <p className="text-lg text-center max-w-3xl mx-auto opacity-90">
            Powered by Gemini 1.5 Flash - Search and discover news across languages and sources
          </p>
          
          {/* Search form */}
          <div className="mt-8 max-w-3xl mx-auto">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <div className="flex flex-col md:flex-row gap-3">
                  <FormField
                    control={form.control}
                    name="query"
                    render={({ field }) => (
                      <FormItem className="flex-1">
                        <FormControl>
                          <div className="relative">
                            <Search className="absolute left-3 top-3 h-4 w-4 text-white/70" />
                            <Input 
                              placeholder="Search for news..." 
                              {...field} 
                              className="pl-9 py-6 bg-white/10 border-white/20 placeholder:text-white/70 text-white"
                            />
                          </div>
                        </FormControl>
                        <FormMessage className="text-white/90" />
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={form.control}
                    name="language"
                    render={({ field }) => (
                      <FormItem className="w-full md:w-1/4">
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger className="py-6 bg-white/10 border-white/20 text-white">
                              <SelectValue placeholder="Language" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {languageOptions.map((option) => (
                              <SelectItem key={option.value} value={option.value}>
                                <span className="flex items-center">
                                  <span className="mr-2">{option.icon}</span>
                                  {option.label}
                                </span>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  {/* Source filter button */}
                  <Sheet>
                    <SheetTrigger asChild>
                      <Button 
                        type="button" 
                        className="bg-white/20 hover:bg-white/30 text-white border-white/20"
                        size="lg"
                      >
                        <Filter className="h-4 w-4 mr-2" />
                        Sources {selectedSources.length > 0 && `(${selectedSources.length})`}
                      </Button>
                    </SheetTrigger>
                    <SheetContent className="w-full sm:max-w-md">
                      <SheetHeader>
                        <SheetTitle>News Sources</SheetTitle>
                        <SheetDescription>
                          Select your preferred news sources. Leave empty to show all sources.
                        </SheetDescription>
                      </SheetHeader>
                      <Separator className="my-4" />
                      <ScrollArea className="h-[70vh] pr-4">
                        <div className="grid grid-cols-1 gap-2 py-4">
                          {availableSources.length > 0 ? (
                            availableSources.map((source) => (
                              <div key={source} className="flex items-center space-x-2">
                                <Checkbox 
                                  id={source} 
                                  checked={selectedSources.includes(source)}
                                  onCheckedChange={() => toggleSource(source)}
                                />
                                <label 
                                  htmlFor={source} 
                                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                >
                                  {source}
                                </label>
                              </div>
                            ))
                          ) : (
                            <div className="text-center py-4">
                              {isServerWarming ? (
                                <div className="flex flex-col items-center gap-2">
                                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                  <p className="text-muted-foreground">Server warming up, please wait...</p>
                                </div>
                              ) : (
                                <p className="text-muted-foreground">No sources available</p>
                              )}
                            </div>
                          )}
                        </div>
                      </ScrollArea>
                      <SheetFooter className="sm:justify-between pt-4 flex-row">
                        <Button 
                          type="button" 
                          variant="outline"
                          onClick={() => {
                            setSelectedSources([]);
                            form.setValue("preferred_sources", []);
                          }}
                          disabled={selectedSources.length === 0}
                        >
                          Clear All
                        </Button>
                        <SheetClose asChild>
                          <Button type="button">Done</Button>
                        </SheetClose>
                      </SheetFooter>
                    </SheetContent>
                  </Sheet>
                </div>
                
                <div className="flex justify-center">
                  <Button 
                    type="submit" 
                    size="lg" 
                    className="px-8 bg-white text-blue-700 hover:bg-white/90"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Searching...
                      </>
                    ) : (
                      <>
                        Search <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </Form>
          </div>
        </div>
      </div>

      <div className="container mx-auto max-w-5xl px-4 py-8">
        {/* Server warming up warning */}
        <ServerWarmupWarning 
          isVisible={isServerWarming} 
          onRetry={handleRetry} 
        />
        
        {/* Mobile source filter chips */}
        {selectedSources.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-2">
            <span className="text-sm text-muted-foreground py-1">Filtered sources:</span>
            {selectedSources.map(source => (
              <Badge key={source} variant="secondary" className="px-2 py-1">
                {source}
                <button 
                  onClick={() => toggleSource(source)} 
                  className="ml-1 text-muted-foreground hover:text-foreground"
                >
                  ×
                </button>
              </Badge>
            ))}
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-6 text-xs" 
              onClick={() => {
                setSelectedSources([]);
                form.setValue("preferred_sources", []);
              }}
            >
              Clear all
            </Button>
          </div>
        )}

        {/* Error message */}
        {error && !isServerWarming && (
          <Alert variant="destructive" className="mb-6">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Search results info */}
        {message && !error && (
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">Search Results</h2>
            <div className="flex items-center justify-between">
              <p className="text-muted-foreground">{message}</p>
              {totalFound > 0 && (
                <p className="text-sm text-muted-foreground">
                  Showing page {currentPage} of {totalPages}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Loading skeletons */}
        {loading && (
          <div className="space-y-6">
            <div className="text-center mb-4">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                {isServerWarming 
                  ? "Connecting to server... This may take up to 30 seconds if the server was inactive."
                  : "Searching for articles..."}
              </p>
            </div>
            
            {Array.from({ length: 3 }).map((_, i) => (
              <Card key={i} className="overflow-hidden">
                <div className="md:flex">
                  <div className="md:w-1/3 h-48 md:h-auto">
                    <Skeleton className="h-full w-full" />
                  </div>
                  <div className="md:w-2/3">
                    <CardHeader className="pb-2">
                      <Skeleton className="h-4 w-20" />
                      <Skeleton className="h-6 w-full mt-2" />
                      <Skeleton className="h-4 w-28 mt-1" />
                    </CardHeader>
                    <CardContent className="pb-2">
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-3/4" />
                    </CardContent>
                    <CardFooter className="pt-2">
                      <Skeleton className="h-9 w-28" />
                    </CardFooter>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Articles list */}
        {!loading && articles.length > 0 && (
          <div className="space-y-6">
            <AnimatePresence>
              {articles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </AnimatePresence>
            
            {/* Pagination controls */}
            <Pagination 
              currentPage={currentPage} 
              totalPages={totalPages} 
              onPageChange={handlePageChange} 
            />
          </div>
        )}

        {/* No results message */}
        {!loading && articles.length === 0 && message && !isServerWarming && (
          <div className="text-center py-12">
            <Globe className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-xl font-medium mb-2">No articles found</h3>
            <p className="text-muted-foreground mb-6">
              Try adjusting your search query or language selection
            </p>
            <Button 
              variant="outline" 
              onClick={() => form.reset()} 
              className="mx-auto"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset search
            </Button>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-8 mt-12">
        <div className="container mx-auto max-w-5xl px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <h3 className="text-lg font-semibold mb-2">News Search</h3>
              <p className="text-slate-400 text-sm">
                Cutting-edge multilingual news search powered by Gemini 1.5 Flash
              </p>
            </div>
            <div className="flex space-x-4">
              <Button variant="ghost" size="sm" className="text-white">
                About
              </Button>
              <Button variant="ghost" size="sm" className="text-white">
                Privacy
              </Button>
              <Button variant="ghost" size="sm" className="text-white">
                Contact
              </Button>
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-slate-800 text-center text-sm text-slate-500">
            © {new Date().getFullYear()} News Search - Powered by Gemini
          </div>
        </div>
      </footer>
    </div>
  );
}