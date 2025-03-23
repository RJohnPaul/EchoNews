"use client";

import { useState, useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// Define form schema with Zod
const formSchema = z.object({
  query: z.string().min(3, {
    message: "Query must be at least 3 characters",
  }),
  language: z.string({
    required_error: "Please select a language",
  }),
  max_articles: z.number().min(1).max(20),
  preferred_sources: z.array(z.string()).optional(),
});

// Define the types
interface NewsSource {
  name: string;
  url?: string;
}

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  source: NewsSource;
  published_date: string;
  link: string;
}

interface NewsResponse {
  articles: NewsArticle[];
  message: string;
  total_found: number;
  available_sources: string[];
}

export default function NewsQueryPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  const [totalFound, setTotalFound] = useState<number>(0);

  // Initialize form with react-hook-form and zod validation
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      query: "",
      language: "en",
      max_articles: 5,
      preferred_sources: [],
    },
  });

  // Watch for language changes to fetch available sources
  const selectedLanguage = form.watch("language");
  
  // Fetch available sources when language changes
  useEffect(() => {
    const fetchSources = async () => {
      try {
        const response = await fetch(`/api/news/sources/${selectedLanguage}`);
        if (response.ok) {
          const data = await response.json();
          setAvailableSources(data.sources.map((s: any) => s.name));
          // Reset preferred sources when language changes
          form.setValue("preferred_sources", []);
        } else {
          console.error("Failed to fetch sources");
        }
      } catch (err) {
        console.error("Error fetching sources:", err);
      }
    };

    if (selectedLanguage) {
      fetchSources();
    }
  }, [selectedLanguage, form]);

  // Handle form submission
  async function onSubmit(values: z.infer<typeof formSchema>) {
    setLoading(true);
    setError(null);
    setArticles([]);
    setMessage("");
    setTotalFound(0);

    try {
      const response = await fetch("/api/news", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: values.query,
          language: values.language,
          max_articles: values.max_articles,
          preferred_sources: values.preferred_sources || [],
        }),
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data: NewsResponse = await response.json();
      
      if (data.articles && data.articles.length > 0) {
        setArticles(data.articles);
        setMessage(data.message);
        setTotalFound(data.total_found);
        
        if (data.available_sources) {
          setAvailableSources(data.available_sources);
        }
      } else {
        setMessage(data.message || "No articles found for your query.");
        setTotalFound(0);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    } finally {
      setLoading(false);
    }
  }

  const languageOptions = [
    { value: "en", label: "English" },
    { value: "hi", label: "Hindi" },
    { value: "ta", label: "Tamil" },
    { value: "te", label: "Telugu" },
  ];

  return (
    <div className="min-h-screen p-8 bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="container mx-auto max-w-5xl">
        <h1 className="text-4xl font-bold mb-8 text-center">Multilingual News Search</h1>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Search for News</CardTitle>
            <CardDescription>
              Enter a topic to search for news articles in your preferred language
            </CardDescription>
          </CardHeader>

          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="query"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Search Query</FormLabel>
                      <FormControl>
                        <Input placeholder="Enter search terms (e.g. 'cricket', 'politics')" {...field} />
                      </FormControl>
                      <FormDescription>
                        What news topic are you interested in?
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="language"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Language</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a language" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {languageOptions.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Choose the language for your news results
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="max_articles"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Maximum Articles: {field.value}</FormLabel>
                      <FormControl>
                        <Slider
                          defaultValue={[field.value]}
                          min={1}
                          max={20}
                          step={1}
                          onValueChange={(vals) => {
                            field.onChange(vals[0]);
                          }}
                        />
                      </FormControl>
                      <FormDescription>
                        How many articles do you want to see? (1-20)
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="preferred_sources"
                  render={() => (
                    <FormItem>
                      <div className="mb-4">
                        <FormLabel className="text-base">Preferred News Sources</FormLabel>
                        <FormDescription>
                          Select news sources you prefer (optional)
                        </FormDescription>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {availableSources.map((source) => (
                          <FormField
                            key={source}
                            control={form.control}
                            name="preferred_sources"
                            render={({ field }) => {
                              return (
                                <FormItem
                                  key={source}
                                  className="flex flex-row items-start space-x-2 space-y-0"
                                >
                                  <FormControl>
                                    <Checkbox
                                      checked={field.value?.includes(source)}
                                      onCheckedChange={(checked) => {
                                        const current = field.value || [];
                                        const updated = checked
                                          ? [...current, source]
                                          : current.filter((val) => val !== source);
                                        field.onChange(updated);
                                      }}
                                    />
                                  </FormControl>
                                  <FormLabel className="text-sm font-normal">
                                    {source}
                                  </FormLabel>
                                </FormItem>
                              );
                            }}
                          />
                        ))}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Button type="submit" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    "Search News"
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {message && !error && (
          <Alert className="mb-6">
            <AlertTitle>Information</AlertTitle>
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}

        {articles.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">
              Search Results {totalFound > articles.length ? `(Showing ${articles.length} of ${totalFound})` : ''}
            </h2>
            {articles.map((article) => (
              <Card key={article.id}>
                <CardHeader>
                  <CardTitle>{article.title}</CardTitle>
                  <CardDescription>
                    {article.source.name} • {new Date(article.published_date).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p>{article.summary}</p>
                </CardContent>
                <CardFooter>
                  <Button variant="outline" asChild>
                    <a href={article.link} target="_blank" rel="noopener noreferrer">
                      Read more
                    </a>
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}