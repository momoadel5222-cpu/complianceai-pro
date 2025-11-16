import { useEffect } from 'react';

const DisqusComments = () => {
  useEffect(() => {
    // Load Disqus script
    const script = document.createElement('script');
    script.src = 'https://your-disqus-shortname.disqus.com/embed.js';
    script.setAttribute('data-timestamp', +new Date());
    script.async = true;
    document.body.appendChild(script);

    return () => {
      // Cleanup
      document.body.removeChild(script);
    };
  }, []);

  return (
    <div style={{ marginTop: '2rem', padding: '1rem' }}>
      <h3>Comments & Feedback</h3>
      <div id="disqus_thread" />
    </div>
  );
};

export default DisqusComments;
