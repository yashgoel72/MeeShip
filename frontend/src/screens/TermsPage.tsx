import { Link } from 'react-router-dom'
import Layout from '../components/Layout'

export default function TermsPage() {
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
            Terms & Conditions
          </h1>
          
          <p className="text-sm text-slate-500">
            Last updated: January 20, 2026
          </p>

          <p>
            Welcome to MeeShip. By accessing or using our AI-powered image optimization service 
            ("Service"), you agree to be bound by these Terms & Conditions ("Terms"). Please read 
            them carefully before using our Service.
          </p>

          <h2>1. Service Description</h2>
          <p>
            MeeShip provides an AI-powered image optimization tool designed specifically for 
            Meesho sellers. Our Service processes product images to generate shipping-optimized 
            variants that comply with Meesho's packaging guidelines, potentially reducing shipping 
            costs per order.
          </p>

          <h2>2. Eligibility & Account</h2>
          <p>
            You must be at least 18 years old to use our Service. By creating an account, you 
            represent that the information you provide is accurate and complete. You are responsible 
            for maintaining the confidentiality of your account credentials and for all activities 
            under your account.
          </p>

          <h2>3. Credit System & Payments</h2>
          <p>
            MeeShip operates on a prepaid credit system. Credits are purchased in packs and are 
            consumed when you generate optimized images. All payments are processed securely 
            through Razorpay, a PCI-DSS compliant payment gateway. Prices are displayed in Indian 
            Rupees (INR) and are inclusive of applicable taxes unless stated otherwise.
          </p>
          <p>
            Credits are non-transferable and are tied to your account. Each credit pack has a 
            validity period as specified at the time of purchase. Unused credits expire at the 
            end of the validity period.
          </p>

          <h2>4. Acceptable Use</h2>
          <p>You agree to use our Service only for lawful purposes. You shall not:</p>
          <ul>
            <li>Upload images that infringe on intellectual property rights of others</li>
            <li>Upload illegal, obscene, defamatory, or harmful content</li>
            <li>Attempt to reverse-engineer, decompile, or extract our AI models</li>
            <li>Use automated scripts or bots to access the Service</li>
            <li>Resell or redistribute generated images as a competing service</li>
          </ul>

          <h2>5. Intellectual Property</h2>
          <p>
            You retain ownership of the original images you upload. The optimized images generated 
            by our Service are licensed to you for use on Meesho and similar e-commerce platforms. 
            MeeShip retains all rights to the underlying AI technology, algorithms, and software.
          </p>

          <h2>6. Disclaimer of Warranties</h2>
          <p>
            Our Service is provided "as is" without warranties of any kind. While we strive to 
            provide accurate shipping-optimized images, we do not guarantee specific shipping 
            cost reductions, as final shipping charges depend on Meesho's policies and carrier 
            rates which are beyond our control.
          </p>

          <h2>7. Limitation of Liability</h2>
          <p>
            To the maximum extent permitted by law, MeeShip shall not be liable for any indirect, 
            incidental, special, or consequential damages arising from your use of the Service. 
            Our total liability shall not exceed the amount you paid for the Service in the 
            preceding 12 months.
          </p>

          <h2>8. Modifications</h2>
          <p>
            We reserve the right to modify these Terms at any time. Continued use of the Service 
            after changes constitutes acceptance of the modified Terms. We will notify registered 
            users of material changes via email.
          </p>

          <h2>9. Governing Law</h2>
          <p>
            These Terms are governed by the laws of India. Any disputes shall be subject to the 
            exclusive jurisdiction of courts in Bangalore, Karnataka.
          </p>

          <h2>10. Contact</h2>
          <p>
            For questions about these Terms, please contact us at{' '}
            <a href="mailto:meeship.seller@gmail.com" className="text-meesho hover:underline">
              meeship.seller@gmail.com
            </a>
          </p>
        </article>
      </div>
    </Layout>
  )
}
