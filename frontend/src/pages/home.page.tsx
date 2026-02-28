import { motion, useScroll, useTransform } from 'framer-motion';
import { upAndDown } from '../component/upAndDown.componet';

const features = [
  { 
    title: "Behavioral Analysis", 
    description: "leverage AI to analyze user behavior and detect anomalies in real-time.", 
    url: "/login" 
  },
  { title: "KYC Automation", description: "Automated identity verification and compliance checks.", url: "/register" },
  { title: "Global Compliance", description: "Built-in KYC and AML automation.",url: "" },
  { title: "Merchant Tools", description: "Customizable checkout experiences.", url: "" },
];

export default function HomePage() {
  const { scrollYProgress } = useScroll();
  const opacity = useTransform(scrollYProgress, [0, 0.9], [1, 0]);

  return (
    <div className="h-screen w-screen overflow-y-scroll snap-y snap-mandatory scroll-smooth bg-white relative">
      
      <motion.div 
        style={{ opacity }}
        className="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 pointer-events-none flex flex-col items-center gap-3"
      >
        <span className="text-[10px] uppercase tracking-[0.3em] text-gray-400 font-bold">
          Keep Scrolling
        </span>
        <div className="w-px h-12 bg-gray-200 relative overflow-hidden">
          <motion.div 
            animate={{ y: [-48, 48] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
            className="w-full h-full bg-blue-600"
          />
        </div>
      </motion.div>

      <section className="h-screen w-full flex flex-col items-center justify-center p-10 snap-start bg-slate-50 relative">
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-7xl font-semibold text-gray-800 mb-6 text-center"
        >
          Welcome to PayShield
        </motion.h1>
        
        <div className="mt-4">
          {upAndDown("Protecting your future")}
        </div>
      </section>

      {features.map((feature, index) => (
        <section 
          key={index} 
          className="h-screen w-full flex items-center justify-center p-10 snap-start border-t border-gray-100 bg-white"
        >
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            viewport={{ amount: 0.5 }}
            className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-2 gap-20 items-center"
          >
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <span className="w-8 h-[2px] bg-blue-600"></span>
                <span className="text-blue-600 font-bold tracking-widest uppercase text-xs">
                  Solution 0{index + 1}
                </span>
              </div>
              <h2 className="text-6xl font-bold text-gray-900 tracking-tight">{feature.title}</h2>
              <p className="text-lg text-gray-500 leading-relaxed max-w-md">{feature.description}</p>
              <a href={feature.url} className="text-blue-600 font-semibold hover:underline transition-all duration-200">Learn more</a>
            </div>
            
            <div className="relative group hover:scale-105 transition-transform duration-300">
              <div className="absolute -inset-4 bg-linear-to-tr from-blue-50 to-indigo-50 rounded-[40px] z-0 opacity-50 group-hover:opacity-100 transition-opacity" />
              <div className="relative h-112.5 bg-white rounded-3xl border border-gray-100 shadow-2xl flex items-center justify-center overflow-hidden">
                 <div className="w-24 h-24 bg-blue-50 rounded-full animate-pulse" />
                 <span className="absolute bottom-8 text-gray-300 text-sm font-mono">ASSET_CONTAINER_{index + 1}</span>
              </div>
            </div>
          </motion.div>
        </section>
      ))}
    </div>
  );
}