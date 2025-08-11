'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Bot,
  Send,
  Lightbulb,
  FileText,
  Wand2,
  MessageCircle,
  Sparkles,
  Zap,
  Brain,
  Target,
  TrendingUp,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  Info
} from 'lucide-react';

interface AIMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  suggestions?: string[];
  actions?: Array<{
    label: string;
    action: string;
    data?: Record<string, unknown>;
  }>;
}

interface AISuggestion {
  id: string;
  type: 'improvement' | 'content' | 'seo' | 'structure';
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  impact: string;
  action?: () => void;
}

interface DocumentationAIProps {
  documentId?: string;
  content?: string;
  onContentUpdate?: (content: string) => void;
  onSuggestionApply?: (suggestion: AISuggestion) => void;
}

const DocumentationAI: React.FC<DocumentationAIProps> = ({
  documentId,
  content = '',
  onContentUpdate,
  onSuggestionApply
}) => {
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'suggestions' | 'insights'>('chat');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize with welcome message
    if (messages.length === 0) {
      setMessages([{
        id: '1',
        type: 'ai',
        content: "Hi! I'm your AI documentation assistant. I can help you improve your content, suggest better structure, optimize for SEO, and answer questions about documentation best practices. How can I help you today?",
        timestamp: new Date(),
        suggestions: [
          "Analyze my document for improvements",
          "Help me write better content",
          "Suggest SEO optimizations",
          "Check document structure"
        ]
      }]);
    }
  }, [messages.length]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const analyzeContent = useCallback(async () => {
    if (!content) return;

    setIsAnalyzing(true);
    try {
      const response = await fetch('/api/documentation/ai/analyze/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          document_id: documentId
        })
      });

      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Error analyzing content:', error);
    } finally {
      setIsAnalyzing(false);
    }
  }, [content, documentId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (content && content.length > 100) {
      analyzeContent();
    }
  }, [content, analyzeContent]);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: AIMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/documentation/ai/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          context: {
            document_id: documentId,
            content: content.substring(0, 1000), // Send first 1000 chars for context
            previous_messages: messages.slice(-5) // Last 5 messages for context
          }
        })
      });

      const data = await response.json();

      const aiMessage: AIMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
        suggestions: data.suggestions,
        actions: data.actions
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: AIMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: "I'm sorry, I encountered an error. Please try again.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
    sendMessage();
  };

  const applySuggestion = (suggestion: AISuggestion) => {
    if (onSuggestionApply) {
      onSuggestionApply(suggestion);
    }
    
    // Remove applied suggestion
    setSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
    
    // Add confirmation message
    const confirmMessage: AIMessage = {
      id: Date.now().toString(),
      type: 'ai',
      content: `Great! I've applied the suggestion: "${suggestion.title}". The changes should improve your document's ${suggestion.type}.`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, confirmMessage]);
  };

  const generateContent = async (prompt: string) => {
    setIsTyping(true);
    try {
      const response = await fetch('/api/documentation/ai/generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          context: content,
          document_id: documentId
        })
      });

      const data = await response.json();
      
      if (onContentUpdate && data.content) {
        onContentUpdate(data.content);
      }

      const aiMessage: AIMessage = {
        id: Date.now().toString(),
        type: 'ai',
        content: `I've generated content based on your request. ${data.explanation || 'The content has been added to your document.'}`,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error generating content:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high': return <AlertCircle className="w-4 h-4" />;
      case 'medium': return <Info className="w-4 h-4" />;
      case 'low': return <CheckCircle className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-96 flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">AI Assistant</h3>
            {isAnalyzing && (
              <div className="flex items-center space-x-1 text-sm text-blue-600">
                <Sparkles className="w-4 h-4 animate-pulse" />
                <span>Analyzing...</span>
              </div>
            )}
          </div>
          
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-3 py-1 rounded text-sm ${
                activeTab === 'chat' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <MessageCircle className="w-4 h-4 inline mr-1" />
              Chat
            </button>
            <button
              onClick={() => setActiveTab('suggestions')}
              className={`px-3 py-1 rounded text-sm ${
                activeTab === 'suggestions' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Lightbulb className="w-4 h-4 inline mr-1" />
              Suggestions ({suggestions.length})
            </button>
            <button
              onClick={() => setActiveTab('insights')}
              className={`px-3 py-1 rounded text-sm ${
                activeTab === 'insights' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Brain className="w-4 h-4 inline mr-1" />
              Insights
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' && (
          <div className="h-full flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                    
                    {message.suggestions && (
                      <div className="mt-2 space-y-1">
                        {message.suggestions.map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => handleSuggestionClick(suggestion)}
                            className="block w-full text-left text-xs p-2 bg-white bg-opacity-20 rounded hover:bg-opacity-30 transition-colors"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                    
                    {message.actions && (
                      <div className="mt-2 space-y-1">
                        {message.actions.map((action, index) => (
                          <button
                            key={index}
                            onClick={() => {
                              if (action.action === 'generate_content') {
                                generateContent(action.data?.prompt || '');
                              }
                            }}
                            className="block w-full text-left text-xs p-2 bg-white bg-opacity-20 rounded hover:bg-opacity-30 transition-colors"
                          >
                            <Wand2 className="w-3 h-3 inline mr-1" />
                            {action.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 p-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Ask me anything about your documentation..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isTyping}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'suggestions' && (
          <div className="h-full overflow-y-auto p-4">
            {suggestions.length > 0 ? (
              <div className="space-y-3">
                {suggestions.map((suggestion) => (
                  <div key={suggestion.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(suggestion.priority)}`}>
                            {getPriorityIcon(suggestion.priority)}
                            <span className="ml-1 capitalize">{suggestion.priority}</span>
                          </span>
                          <span className="text-xs text-gray-500 capitalize">{suggestion.type}</span>
                        </div>
                        <h4 className="font-medium text-gray-900 mb-1">{suggestion.title}</h4>
                        <p className="text-sm text-gray-600 mb-2">{suggestion.description}</p>
                        <p className="text-xs text-blue-600">{suggestion.impact}</p>
                      </div>
                      <button
                        onClick={() => applySuggestion(suggestion)}
                        className="ml-4 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Lightbulb className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No suggestions yet</h3>
                <p className="text-gray-600 mb-4">Start writing content to get AI-powered suggestions for improvement.</p>
                <button
                  onClick={analyzeContent}
                  disabled={!content || isAnalyzing}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <Zap className="w-4 h-4 inline mr-2" />
                  Analyze Content
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="h-full overflow-y-auto p-4">
            <div className="space-y-4">
              {/* Content Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-900">Word Count</span>
                  </div>
                  <p className="text-lg font-bold text-blue-900 mt-1">
                    {content.split(/\s+/).filter(word => word.length > 0).length}
                  </p>
                </div>
                
                <div className="bg-green-50 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-900">Read Time</span>
                  </div>
                  <p className="text-lg font-bold text-green-900 mt-1">
                    {Math.ceil(content.split(/\s+/).length / 200)} min
                  </p>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Quick Actions</h4>
                <div className="grid grid-cols-1 gap-2">
                  <button
                    onClick={() => generateContent('Improve the readability and structure of this content')}
                    className="flex items-center space-x-2 p-2 text-left text-sm bg-gray-50 rounded hover:bg-gray-100"
                  >
                    <Target className="w-4 h-4 text-gray-600" />
                    <span>Improve Readability</span>
                  </button>
                  
                  <button
                    onClick={() => generateContent('Add SEO-optimized headings and structure')}
                    className="flex items-center space-x-2 p-2 text-left text-sm bg-gray-50 rounded hover:bg-gray-100"
                  >
                    <TrendingUp className="w-4 h-4 text-gray-600" />
                    <span>Optimize for SEO</span>
                  </button>
                  
                  <button
                    onClick={() => generateContent('Make this content more engaging for the target audience')}
                    className="flex items-center space-x-2 p-2 text-left text-sm bg-gray-50 rounded hover:bg-gray-100"
                  >
                    <Users className="w-4 h-4 text-gray-600" />
                    <span>Enhance Engagement</span>
                  </button>
                </div>
              </div>

              {/* Content Health */}
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Content Health</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Structure</span>
                    <div className="flex items-center space-x-1">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div className="bg-green-500 h-2 rounded-full" style={{ width: '80%' }}></div>
                      </div>
                      <span className="text-xs text-gray-500">Good</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Readability</span>
                    <div className="flex items-center space-x-1">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '60%' }}></div>
                      </div>
                      <span className="text-xs text-gray-500">Fair</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">SEO Score</span>
                    <div className="flex items-center space-x-1">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div className="bg-red-500 h-2 rounded-full" style={{ width: '40%' }}></div>
                      </div>
                      <span className="text-xs text-gray-500">Needs Work</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentationAI;