import { motion } from 'framer-motion';

export function upAndDown(text: string) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ 
        opacity: 1,
        y: [0, -12, 0],
      }}
      transition={{ 
        opacity: { delay: 0.5, duration: 1 },
        y: { 
          repeat: Infinity, 
          duration: 2, 
          ease: "easeInOut" 
        } 
      }}
      className="flex flex-col items-center gap-2 mt-8"
    >
      <p className="text-lg font-medium text-gray-500">
        {text}
      </p>
      <span className="text-2xl text-blue-600">↓</span>
    </motion.div>
  )
}