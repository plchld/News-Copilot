# Main Brief & Story Deep-Dive Implementation Guide

## After Onboarding: The Daily Brief View

### Core Concept
Users land on their personalized brief - a finite, complete package. Not a feed. A beginning, middle, and end.

### Brief Canvas Structure
```jsx
// app/(main)/brief/page.tsx

/* The header is critical - it sets the "finite" expectation */
<header className="fixed top-0 inset-x-0 z-40 bg-black/80 backdrop-blur-xl border-b border-white/[0.05]">
  <div className="max-w-4xl mx-auto px-6 py-4">
    <div className="flex items-center justify-between">
      {/* Date and brief info */}
      <div>
        <p className="text-xs text-white/40 uppercase tracking-wider">
          {format(new Date(), 'EEEE, MMMM d')}
        </p>
        <h1 className="text-lg font-serif text-white/90 mt-1">
          Your Brief • 5 stories • 5 min
        </h1>
      </div>
      
      {/* Mode toggle - both are equal citizens */}
      <div className="flex items-center gap-2 p-1 bg-white/[0.03] rounded-xl">
        <button 
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-all
            ${mode === 'audio' 
              ? 'bg-white/10 text-white' 
              : 'text-white/60 hover:text-white/80'}
          `}
        >
          <span className="flex items-center gap-2">
            <Headphones className="w-4 h-4" />
            Audio
          </span>
        </button>
        <button 
          className={`
            px-4 py-2 rounded-lg text-sm font-medium transition-all
            ${mode === 'read' 
              ? 'bg-white/10 text-white' 
              : 'text-white/60 hover:text-white/80'}
          `}
        >
          <span className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            Read
          </span>
        </button>
      </div>
    </div>
  </div>
</header>

/* Main content area */
<main className="pt-24 pb-32 min-h-screen">
  <div className="max-w-4xl mx-auto px-6">
    {/* Story cards */}
    <div className="space-y-4">
      {stories.map((story, index) => (
        <StoryCard 
          key={story.id} 
          story={story} 
          index={index}
          isPlaying={audioMode && currentStoryIndex === index}
        />
      ))}
    </div>
    
    {/* Completion state - critical for finite feel */}
    <div className="mt-16 text-center">
      <div className="inline-flex items-center gap-3 px-6 py-3 bg-white/[0.03] rounded-full">
        <CheckCircle className="w-5 h-5 text-green-500/70" />
        <span className="text-white/60 text-sm">
          That's everything for today
        </span>
      </div>
    </div>
  </div>
</main>
```

### Story Card Component - The Gateway to Depth
```jsx
// components/brief/StoryCard.tsx

const StoryCard = ({ story, index, isPlaying }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <motion.article
      layout
      className={`
        relative overflow-hidden cursor-pointer
        ${isExpanded ? 'fixed inset-0 z-50' : 'relative'}
      `}
      onClick={() => !isExpanded && setIsExpanded(true)}
    >
      {/* Card in collapsed state */}
      {!isExpanded ? (
        <div className={`
          group p-6 bg-white/[0.02] rounded-2xl border border-white/[0.05]
          hover:bg-white/[0.03] hover:border-white/[0.08] transition-all duration-300
          ${isPlaying ? 'ring-2 ring-white/20 ring-offset-4 ring-offset-black' : ''}
        `}>
          {/* Category and time */}
          <div className="flex items-center justify-between mb-3">
            <span className={`
              text-xs font-medium uppercase tracking-wider
              ${getCategoryColor(story.category)}
            `}>
              {story.category}
            </span>
            <span className="text-xs text-white/40">
              {story.readTime} min read
            </span>
          </div>
          
          {/* Headline */}
          <h2 className="text-xl font-serif text-white/90 leading-tight mb-3 line-clamp-2 group-hover:text-white transition-colors">
            {story.headline}
          </h2>
          
          {/* Summary */}
          <p className="text-white/60 leading-relaxed line-clamp-3 text-sm">
            {story.summary}
          </p>
          
          {/* Depth indicators - subtle promise of more */}
          <div className="flex items-center gap-4 mt-4">
            {story.hasTimeline && (
              <div className="flex items-center gap-1.5 text-white/30">
                <Clock className="w-3.5 h-3.5" />
                <span className="text-xs">Timeline</span>
              </div>
            )}
            {story.hasPerspectives && (
              <div className="flex items-center gap-1.5 text-white/30">
                <BarChart3 className="w-3.5 h-3.5" />
                <span className="text-xs">Perspectives</span>
              </div>
            )}
            {story.socialPulse && (
              <div className="flex items-center gap-1.5 text-white/30">
                <MessageCircle className="w-3.5 h-3.5" />
                <span className="text-xs">Social pulse</span>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Expanded state - full story view */
        <ExpandedStoryView 
          story={story} 
          onClose={() => setIsExpanded(false)} 
        />
      )}
    </motion.article>
  );
};
```

## Expanded Story View - Progressive Depth

### The Expansion Animation
```jsx
// components/story/ExpandedStoryView.tsx

const ExpandedStoryView = ({ story, onClose }) => {
  const [activeTab, setActiveTab] = useState('story');
  const [showJargonExplanation, setShowJargonExplanation] = useState(null);
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-black overflow-y-auto"
    >
      {/* Header with back button */}
      <header className="sticky top-0 z-10 bg-black/90 backdrop-blur-xl border-b border-white/[0.05]">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-white/60 hover:text-white/90 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to brief</span>
          </button>
          
          {/* Follow story button */}
          <button className="flex items-center gap-2 px-4 py-2 bg-white/[0.05] hover:bg-white/[0.08] rounded-lg transition-colors">
            <Bell className="w-4 h-4" />
            <span className="text-sm">Follow story</span>
          </button>
        </div>
      </header>
      
      {/* Main content */}
      <main className="max-w-3xl mx-auto px-6 py-12">
        {/* Category and metadata */}
        <div className="flex items-center gap-4 mb-6">
          <span className={`
            text-xs font-medium uppercase tracking-wider
            ${getCategoryColor(story.category)}
          `}>
            {story.category}
          </span>
          <span className="text-xs text-white/40">
            {story.readTime} min read • Updated {story.lastUpdated}
          </span>
        </div>
        
        {/* Headline */}
        <h1 className="text-4xl md:text-5xl font-serif text-white leading-tight mb-8">
          {story.headline}
        </h1>
        
        {/* Full summary with jargon detection */}
        <div className="prose prose-invert prose-lg max-w-none">
          <JargonText 
            content={story.fullSummary}
            onJargonClick={setShowJargonExplanation}
          />
        </div>
        
        {/* Progressive depth tabs */}
        <div className="mt-12">
          <TabNavigation 
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            availableTabs={getAvailableTabs(story)}
          />
          
          <div className="mt-8">
            {activeTab === 'story' && <StoryContent story={story} />}
            {activeTab === 'timeline' && <TimelineView timeline={story.timeline} />}
            {activeTab === 'perspectives' && <PerspectivesView perspectives={story.perspectives} />}
            {activeTab === 'social' && <SocialPulseView socialData={story.socialPulse} />}
          </div>
        </div>
      </main>
      
      {/* Jargon explanation modal */}
      <JargonModal 
        term={showJargonExplanation}
        onClose={() => setShowJargonExplanation(null)}
      />
    </motion.div>
  );
};
```

### Jargon Detection & Explanation System
```jsx
// components/story/JargonText.tsx

const JargonText = ({ content, onJargonClick }) => {
  // Parse content and wrap jargon terms
  const renderContent = () => {
    return content.split(' ').map((word, i) => {
      const jargonTerm = detectJargon(word);
      if (jargonTerm) {
        return (
          <span key={i}>
            <button
              onClick={() => onJargonClick(jargonTerm)}
              className="relative inline-block group"
            >
              <span className="border-b border-dotted border-white/40 group-hover:border-white/60 transition-colors">
                {word}
              </span>
              {/* Subtle hint on hover */}
              <span className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-white/10 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                Tap to explain
              </span>
            </button>
            {' '}
          </span>
        );
      }
      return word + ' ';
    });
  };
  
  return <p className="text-white/80 leading-relaxed">{renderContent()}</p>;
};

// Jargon explanation modal
const JargonModal = ({ term, onClose }) => {
  if (!term) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-60 flex items-end justify-center px-6 pb-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="bg-white/[0.08] backdrop-blur-xl rounded-2xl p-6 max-w-md w-full border border-white/[0.1]"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-lg font-medium text-white mb-2">{term.word}</h3>
        <p className="text-white/70 text-sm leading-relaxed mb-4">
          {term.explanation}
        </p>
        <button
          onClick={onClose}
          className="w-full py-3 bg-white/10 hover:bg-white/15 rounded-lg text-sm font-medium transition-colors"
        >
          Got it
        </button>
      </motion.div>
    </motion.div>
  );
};
```

### Timeline Implementation
```jsx
// components/story/TimelineView.tsx

const TimelineView = ({ timeline }) => {
  const [selectedEvent, setSelectedEvent] = useState(null);
  
  return (
    <div className="relative">
      {/* Timeline header */}
      <div className="mb-8">
        <h3 className="text-lg font-medium text-white mb-2">Story Evolution</h3>
        <p className="text-white/60 text-sm">
          How this story developed over time
        </p>
      </div>
      
      {/* Timeline visualization */}
      <div className="relative">
        {/* Base line */}
        <div className="absolute left-8 top-0 bottom-0 w-px bg-white/10" />
        
        {/* Events */}
        <div className="space-y-8">
          {timeline.events.map((event, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="relative flex items-start gap-4"
            >
              {/* Timeline dot */}
              <button
                onClick={() => setSelectedEvent(event)}
                className={`
                  relative z-10 w-4 h-4 rounded-full border-2 transition-all
                  ${selectedEvent?.id === event.id 
                    ? 'bg-white border-white scale-125' 
                    : 'bg-black border-white/40 hover:border-white/60'}
                `}
              >
                {/* Pulse effect for major events */}
                {event.isMajor && (
                  <span className="absolute inset-0 rounded-full bg-white/20 animate-ping" />
                )}
              </button>
              
              {/* Event content */}
              <div className="flex-1">
                <p className="text-xs text-white/40 mb-1">{event.date}</p>
                <h4 className="text-white/90 font-medium mb-1">{event.title}</h4>
                <p className="text-white/60 text-sm">{event.summary}</p>
                
                {/* Expanded details */}
                {selectedEvent?.id === event.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-4 p-4 bg-white/[0.03] rounded-lg"
                  >
                    <p className="text-white/70 text-sm">{event.details}</p>
                  </motion.div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

### Perspectives Spectrum View
```jsx
// components/story/PerspectivesView.tsx

const PerspectivesView = ({ perspectives }) => {
  const [selectedSource, setSelectedSource] = useState(null);
  
  return (
    <div>
      <div className="mb-8">
        <h3 className="text-lg font-medium text-white mb-2">Different Angles</h3>
        <p className="text-white/60 text-sm">
          How various sources frame this story
        </p>
      </div>
      
      {/* Spectrum visualization */}
      <div className="relative h-20 mb-12">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-red-500/10 rounded-lg" />
        
        {/* Spectrum line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/10" />
        
        {/* Source positions */}
        {perspectives.sources.map((source, i) => (
          <motion.button
            key={i}
            className="absolute top-1/2 -translate-y-1/2"
            style={{ left: `${source.position}%` }}
            whileHover={{ scale: 1.2 }}
            onClick={() => setSelectedSource(source)}
          >
            <div className={`
              w-3 h-3 rounded-full bg-white shadow-lg
              ${selectedSource?.id === source.id ? 'ring-4 ring-white/20' : ''}
            `} />
            <span className="absolute top-6 left-1/2 -translate-x-1/2 text-xs text-white/60 whitespace-nowrap">
              {source.name}
            </span>
          </motion.button>
        ))}
        
        {/* Labels */}
        <span className="absolute left-0 top-0 text-xs text-blue-400/80">Progressive</span>
        <span className="absolute right-0 top-0 text-xs text-red-400/80">Conservative</span>
      </div>
      
      {/* Key differences */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
          <h4 className="text-sm font-medium text-blue-400 mb-2">Progressive framing</h4>
          <p className="text-white/70 text-sm italic">"{perspectives.progressiveQuote}"</p>
          <p className="text-white/50 text-xs mt-2">Key terms: {perspectives.progressiveTerms.join(', ')}</p>
        </div>
        
        <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg">
          <h4 className="text-sm font-medium text-red-400 mb-2">Conservative framing</h4>
          <p className="text-white/70 text-sm italic">"{perspectives.conservativeQuote}"</p>
          <p className="text-white/50 text-xs mt-2">Key terms: {perspectives.conservativeTerms.join(', ')}</p>
        </div>
      </div>
      
      {/* Selected source details */}
      {selectedSource && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-4 bg-white/[0.03] rounded-lg"
        >
          <h4 className="font-medium text-white mb-2">{selectedSource.name}'s Coverage</h4>
          <p className="text-white/70 text-sm">{selectedSource.analysis}</p>
        </motion.div>
      )}
    </div>
  );
};
```

### Social Pulse Implementation
```jsx
// components/story/SocialPulseView.tsx

const SocialPulseView = ({ socialData }) => {
  return (
    <div className="space-y-8">
      {/* Trending level */}
      <div className="flex items-center gap-4 p-4 bg-white/[0.03] rounded-lg">
        <div className={`
          w-12 h-12 rounded-lg flex items-center justify-center
          ${socialData.trendingLevel === 'high' ? 'bg-orange-500/20' : 
            socialData.trendingLevel === 'medium' ? 'bg-yellow-500/20' : 
            'bg-gray-500/20'}
        `}>
          <TrendingUp className={`
            w-6 h-6
            ${socialData.trendingLevel === 'high' ? 'text-orange-400' : 
              socialData.trendingLevel === 'medium' ? 'text-yellow-400' : 
              'text-gray-400'}
          `} />
        </div>
        <div>
          <h4 className="text-white font-medium">
            {socialData.trendingLevel === 'high' ? 'Highly Trending' :
             socialData.trendingLevel === 'medium' ? 'Moderately Trending' :
             'Limited Discussion'}
          </h4>
          <p className="text-white/60 text-sm">{socialData.trendingDescription}</p>
        </div>
      </div>
      
      {/* Top question */}
      {socialData.topQuestion && (
        <div className="p-4 bg-white/[0.03] rounded-lg border border-white/[0.05]">
          <div className="flex items-start gap-3">
            <HelpCircle className="w-5 h-5 text-white/40 mt-0.5" />
            <div>
              <p className="text-xs text-white/40 mb-1">Most asked question</p>
              <p className="text-white/90">{socialData.topQuestion}</p>
              {socialData.questionAnswer && (
                <p className="text-white/60 text-sm mt-2">{socialData.questionAnswer}</p>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Common misconception */}
      {socialData.misconception && (
        <div className="p-4 bg-red-500/5 rounded-lg border border-red-500/20">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
            <div>
              <p className="text-xs text-red-400 mb-1">Common misconception</p>
              <p className="text-white/90 mb-2">{socialData.misconception.claim}</p>
              <p className="text-white/60 text-sm">{socialData.misconception.correction}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Sentiment snapshot */}
      {socialData.sentiment && (
        <div>
          <p className="text-xs text-white/40 mb-3">General sentiment</p>
          <div className="space-y-2">
            {Object.entries(socialData.sentiment).map(([label, percentage]) => (
              <div key={label} className="flex items-center gap-3">
                <span className="text-white/60 text-sm w-20">{label}</span>
                <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="h-full bg-white/30"
                  />
                </div>
                <span className="text-white/40 text-sm">{percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

### Audio Player Implementation
```jsx
// components/audio/AudioPlayer.tsx

const AudioPlayer = ({ stories, currentIndex, onStoryChange }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [speed, setSpeed] = useState(1);
  
  return (
    <motion.div
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      className="fixed bottom-0 inset-x-0 z-30 bg-black/90 backdrop-blur-xl border-t border-white/[0.05]"
    >
      <div className="max-w-4xl mx-auto px-6 py-4">
        {/* Progress bar for all stories */}
        <div className="flex gap-1 mb-4">
          {stories.map((_, i) => (
            <div
              key={i}
              className={`
                flex-1 h-1 rounded-full overflow-hidden
                ${i < currentIndex ? 'bg-white/30' : 'bg-white/10'}
              `}
            >
              {i === currentIndex && (
                <motion.div
                  className="h-full bg-white/60"
                  style={{ width: `${progress}%` }}
                />
              )}
            </div>
          ))}
        </div>
        
        {/* Controls */}
        <div className="flex items-center gap-4">
          {/* Play/pause */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="w-12 h-12 bg-white/10 hover:bg-white/15 rounded-full flex items-center justify-center transition-colors"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>
          
          {/* Story info */}
          <div className="flex-1 min-w-0">
            <h4 className="text-white/90 font-medium truncate">
              {stories[currentIndex].headline}
            </h4>
            <p className="text-white/40 text-sm">
              Story {currentIndex + 1} of {stories.length}
            </p>
          </div>
          
          {/* Speed control */}
          <button
            onClick={() => setSpeed(speed === 1 ? 1.5 : speed === 1.5 ? 2 : 1)}
            className="px-3 py-1.5 bg-white/10 hover:bg-white/15 rounded-lg text-sm transition-colors"
          >
            {speed}x
          </button>
          
          {/* Skip */}
          <button
            onClick={() => onStoryChange(currentIndex + 1)}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            disabled={currentIndex >= stories.length - 1}
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};
```

## Critical Implementation Notes

1. **Finite Package Philosophy**: Always show story count, never "load more"
2. **Progressive Disclosure**: Start with 180px cards, expand to full screen
3. **Equal Audio/Text**: Neither mode should feel secondary
4. **Jargon System**: Learn what users know, stop explaining familiar terms
5. **No Infinite Scroll**: Clear beginning and end to the brief
6. **Depth Indicators**: Show what additional layers are available
7. **Smooth Transitions**: Use layout animations for card-to-full expansion
8. **Trust Through Transparency**: Show source count, last updated, corrections
9. **Anti-Viral**: No share buttons, like counts, or engagement metrics
10. **Calm Aesthetic**: Every interaction should lower anxiety, not raise it

This implementation guide maintains all the nuanced design decisions we discussed while providing clear, actionable components for development.