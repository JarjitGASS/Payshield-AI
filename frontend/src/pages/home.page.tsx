import { motion, useScroll, useTransform } from 'framer-motion';
import { upAndDown } from '../component/upAndDown.componet';
import InputBehavioral from '../assets/behavior.png'
import KycOcr from '../assets/kycocr.png'
import GeoIp from '../assets/geoIp.png'
import DeviceFingerprint from '../assets/osFingerprint.webp'
import CompanySentiment from '../assets/company.png'
import NameEntropy from '../assets/nameEntropy.jpg'
import EmailAge from '../assets/emailAge.png'
import MouseClick from '../assets/mouse.png'
import Agentic from '../assets/agentic.webp'

const features = [
  { 
    title: "Behavioral Analysis", 
    description: "Monitor user behavior patterns including mouse movements, clicks, typing speed, and interaction timing to detect anomalies and suspicious activity during login.", 
    url: "/login" ,
    assetSrc: InputBehavioral
  },
  { 
    title: "KYC Automation", 
    description: "Automated identity verification with ID card OCR, NIK validation, email verification, and name entropy analysis to prevent fraud during user registration.", 
    url: "/register",
    assetSrc: KycOcr
  },
  { 
    title: "IP Location Verification", 
    description: "Verify user's declared location against actual IP geolocation to detect location spoofing, VPN usage, and impossible travel patterns.", 
    url: "/geo-ip" ,
    assetSrc: GeoIp
  },
  { 
    title: "Network Fraud Detection", 
    description: "Analyze device fingerprints, network signals, browser type, timezone, screen resolution, and login history to detect bot activity and network-based fraud.", 
    url: "/network-fraud",
    assetSrc: DeviceFingerprint
  },
  { 
    title: "Click Pattern Analysis", 
    description: "Track and analyze user click positions, timing, and movement patterns to build behavioral fingerprints and calculate navigation consistency scores.", 
    url: "/click-test",
    assetSrc: MouseClick
  },
  { 
    title: "Company Sentiment Analysis", 
    description: "Analyze company reputation and sentiment through NLP to assess merchant legitimacy, detect fraud patterns, and identify risky business entities.", 
    url: "/sentiment-entity",
    assetSrc: CompanySentiment
  },
  { 
    title: "Name Entropy Validation", 
    description: "Validate user names using Shannon entropy and n-gram analysis to detect synthetic, suspicious, or randomly generated names.", 
    url: "/name-entropy",
    assetSrc: NameEntropy
  },
  { 
    title: "Email Age Verification", 
    description: "Verify email address validity and check email account age to ensure legitimacy and detect recently created fraud accounts.", 
    url: "/bind-email",
    assetSrc: EmailAge
  },
  { 
    title: "Agentic Risk Assessment", 
    description: "Comprehensive fraud detection engine orchestrating identity, behavioral, and network analysis using AI agents with human-in-the-loop review capability.", 
    url: "/agentic-risk-assessment",
    assetSrc: Agentic
  }
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

              <div className="relative h-112.5 bg-white rounded-3xl border border-gray-100 shadow-2xl flex items-center justify-center">
                <div className="w-24 h-24 bg-blue-50 rounded-full animate-pulse" />

                <div className="absolute inset-0 flex items-center justify-center p-6">
                  <img
                    src={feature.assetSrc}
                    alt="Feature Asset"
                    className="max-h-full max-w-full object-contain"
                  />
                </div>
              </div>
            </div>
          </motion.div>
        </section>
      ))}
    </div>
  );
}