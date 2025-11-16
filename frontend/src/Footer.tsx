export default function Footer() {
  return (
    <footer className="bg-gray-800 text-white py-6 mt-auto">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-center md:text-left">
            <p className="text-sm">
              © 2025 <span className="font-semibold">ComplianceAI Pro</span>. All rights reserved.
            </p>
          </div>
          <div className="text-center md:text-right">
            <p className="text-sm">
              Powered by{' '}
              <span className="font-bold text-blue-400">Mohamed Emam</span>
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Advanced AI-Powered Sanctions Screening
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}

