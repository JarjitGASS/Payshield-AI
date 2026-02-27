import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    confirmPassword: "",
    nik: "",
    fullname: "",
    pob: "",
    dob: "",
    gender: "",
  });
  const [step, setStep] = useState(1); // 1 = Account, 2 = Identity
  const [isError, setIsError] = useState<boolean | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const dataToSend = new FormData();
    Object.entries(formData).forEach(([key, value]) => {
      dataToSend.append(key, value);
    });
    
    const fileInput = e.currentTarget.querySelector('input[name="file"]') as HTMLInputElement;
    if (fileInput && fileInput.files && fileInput.files[0]) {
      dataToSend.append("file", fileInput.files[0]);
    }
    else {
      setIsError(true);
      setMessage("ID Card photo is required!");
      return;
    }

    if (dataToSend.get("password") !== dataToSend.get("confirmPassword")) {
      setIsError(true);
      setMessage("Passwords do not match!");
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/register', {
        method: 'POST',
        body: dataToSend,
      });

      const result = await response.json();
      console.log(result);
      if (!response.ok) {
        setIsError(true);
        if (typeof result.detail === "string") {
          setMessage(result.detail);
          setAnalysis(null);
        } else {
          setMessage(result.detail?.message ?? "Registration failed");
          setAnalysis(result.detail?.analysis ?? null);
        }
        return;
      }
      
      setIsError(!result.success);
      setMessage(result.message);
      setAnalysis(result.analysis || null);
    } catch {
      setIsError(true);
      setMessage("Failed to connect to the server.");
    }
  };

  return (
    <div className="min-h-screen w-screen flex items-center justify-center bg-gray-100 p-6">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-lg">
        {/* Step Indicator */}
        <div className="flex justify-between mb-8 px-4">
          <div className={`h-2 flex-1 rounded-full ${step >= 1 ? 'bg-blue-600' : 'bg-gray-200'}`} />
          <div className="w-4" />
          <div className={`h-2 flex-1 rounded-full ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
        </div>

        <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">
          {step === 1 ? "Create Account" : "Identity Details"}
        </h1>
        <p className="text-center text-gray-500 mb-8">Step {step} of 2</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <AnimatePresence mode="wait">
            {step === 1 ? (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-5"
              >
                <div className="flex flex-col">
                  <label className="text-sm font-semibold text-gray-600 mb-1">Username</label>
                  <input name="username" type="text" required className="p-2 border rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none" placeholder="johndoe123" onChange={handleChange}/>
                </div>
                <div className="flex flex-col">
                  <label className="text-sm font-semibold text-gray-600 mb-1">Password</label>
                  <input name="password" type="password" required className="p-2 border rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none" placeholder="••••••••" onChange={handleChange} />
                </div>
                <div className="flex flex-col">
                  <label className="text-sm font-semibold text-gray-600 mb-1">Confirm Password</label>
                  <input name="confirmPassword" type="password" required className="p-2 border rounded-lg text-black focus:ring-2 focus:ring-blue-500 outline-none" placeholder="••••••••" onChange={handleChange} />
                </div>
                <button 
                  type="button" 
                  onClick={() => setStep(2)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all"
                >
                  Continue
                </button>
              </motion.div>
            ) : (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-5"
              >
                <div className="flex flex-col">
                  <label className="text-sm font-semibold text-gray-600 mb-1">NIK</label>
                  <input name="nik" type="text" required className="p-2 border rounded-lg text-black" placeholder="1234567890123456" onChange={handleChange}/>
                </div>
                <div className="flex flex-col">
                  <label className="text-sm font-semibold text-gray-600 mb-1">Nama Lengkap</label>
                  <input name="fullname" type="text" required className="p-2 border rounded-lg text-black" placeholder="John Doe" onChange={handleChange} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col">
                    <label className="text-sm font-semibold text-gray-600 mb-1">Tempat Lahir</label>
                    <input name="pob" type="text" required className="p-2 border rounded-lg text-black" placeholder="Jakarta" onChange={handleChange}/>
                  </div>
                  <div className="flex flex-col">
                    <label className="text-sm font-semibold text-gray-600 mb-1">Tanggal Lahir</label>
                    <input name="dob" type="date" required className="p-2 border rounded-lg text-black" onChange={handleChange} />
                  </div>
                </div>
                <div className="flex flex-col">
                  <label className="text-sm font-semibold text-gray-600 mb-1">Jenis Kelamin</label>
                  <select name="gender" required className="p-2 border rounded-lg text-black" onChange={handleChange}>
                    <option value="">Pilih...</option>
                    <option value="Laki-laki">Laki-laki</option>
                    <option value="Perempuan">Perempuan</option>
                  </select>
                </div>
                <div className="flex flex-col">
                  <label className="text-sm font-semibold text-gray-600 mb-1">Foto ID Card</label>
                  <input
                    name="file"
                    type="file"
                    accept="image/*"
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:bg-blue-50 file:text-blue-700"
                    required
                  />
                </div>
                <div className="flex gap-3">
                  <button type="button" onClick={() => setStep(1)} className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-600 font-bold py-3 rounded-lg transition-all">
                    Back
                  </button>
                  <button type="submit" className="flex-[2] bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all shadow-lg active:scale-[0.98]">
                    Daftar Sekarang
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </form>

        {isError !== null && (
          <div className={`mt-6 p-4 rounded-lg text-center ${isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {message}
            <p className="w-full max-h-32 overflow-y-auto text-sm">{analysis!=null?JSON.stringify(analysis):null}</p>
          </div>
        )}
      </div>
    </div>
  );
}