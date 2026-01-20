import { Link } from 'react-router-dom'
import Layout from '../components/Layout'

export default function PrivacyPage() {
  return (
    <Layout>
      <div className="mx-auto max-w-3xl px-4 pt-28 pb-16">
        <div className="mb-8">
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-meesho transition-colors"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </Link>
        </div>

        <article className="prose prose-slate max-w-none">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
            Privacy Policy
          </h1>
          
          <p className="text-sm text-slate-500">
            Last updated: January 20, 2026
          </p>

          <p>
            At MeeShip, we are committed to protecting your privacy and handling your data 
            responsibly. This Privacy Policy explains how we collect, use, and safeguard your 
            information when you use our Service.
          </p>

          <h2>1. Information We Collect</h2>
          
          <h3>Account Information</h3>
          <p>
            When you create an account, we collect your email address for authentication purposes. 
            We use a secure passwordless login system via email OTP (One-Time Password).
          </p>

          <h3>Payment Information</h3>
          <p>
            All payment processing is handled by Razorpay, our PCI-DSS compliant payment partner. 
            We do not store your credit/debit card numbers, CVV, or banking details on our servers. 
            We only receive transaction confirmations, order IDs, and payment status from Razorpay 
            to credit your account.
          </p>

          <h3>Images</h3>
          <p>
            When you upload product images for optimization, these images are processed by our 
            AI system. We retain uploaded and generated images only for the duration necessary 
            to deliver the Service (typically 7 days), after which they are automatically deleted 
            from our servers.
          </p>

          <h3>Usage Data</h3>
          <p>
            We collect anonymous usage analytics to improve our Service, including pages visited, 
            features used, and general performance metrics. We use PostHog for privacy-friendly 
            analytics.
          </p>

          <h2>2. How We Use Your Information</h2>
          <ul>
            <li>To provide and maintain our image optimization Service</li>
            <li>To process payments and credit your account</li>
            <li>To send transactional emails (payment receipts, credit notifications)</li>
            <li>To respond to your support requests</li>
            <li>To improve our Service based on usage patterns</li>
            <li>To comply with legal obligations</li>
          </ul>

          <h2>3. Data Sharing</h2>
          <p>
            <strong>We never share, sell, or rent your images or personal data to third parties 
            for marketing purposes.</strong>
          </p>
          <p>Your data is shared only with:</p>
          <ul>
            <li>
              <strong>Razorpay:</strong> For payment processing (subject to{' '}
              <a href="https://razorpay.com/privacy/" target="_blank" rel="noopener noreferrer" className="text-meesho hover:underline">
                Razorpay's Privacy Policy
              </a>)
            </li>
            <li>
              <strong>AI Processing:</strong> Your images are processed through secure AI 
              pipelines. Images are not used to train third-party models and are not accessible 
              to any external parties.
            </li>
            <li>
              <strong>Legal Requirements:</strong> We may disclose information if required by 
              law or to protect our rights
            </li>
          </ul>

          <h2>4. Data Security</h2>
          <p>
            We implement industry-standard security measures including encrypted data transmission 
            (HTTPS/TLS), secure cloud storage, and access controls. However, no method of 
            transmission over the internet is 100% secure.
          </p>

          <h2>5. Data Retention</h2>
          <ul>
            <li><strong>Account data:</strong> Retained while your account is active</li>
            <li><strong>Payment records:</strong> Retained for 7 years for accounting compliance</li>
            <li><strong>Uploaded images:</strong> Deleted within 7 days of processing</li>
            <li><strong>Generated images:</strong> Available for download for 7 days, then deleted</li>
          </ul>

          <h2>6. Your Rights</h2>
          <p>Under applicable Indian data protection laws, you have the right to:</p>
          <ul>
            <li>Access the personal data we hold about you</li>
            <li>Request correction of inaccurate data</li>
            <li>Request deletion of your account and associated data</li>
            <li>Withdraw consent for marketing communications</li>
          </ul>

          <h2>7. Cookies</h2>
          <p>
            We use essential cookies for authentication and session management. We do not use 
            third-party advertising cookies or tracking cookies.
          </p>

          <h2>8. Changes to This Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. We will notify you of material 
            changes via email or a prominent notice on our website.
          </p>

          <h2>9. Contact Us</h2>
          <p>
            For privacy-related questions or to exercise your rights, contact us at{' '}
            <a href="mailto:meeship.seller@gmail.com" className="text-meesho hover:underline">
              meeship.seller@gmail.com
            </a>
          </p>
        </article>
      </div>
    </Layout>
  )
}
