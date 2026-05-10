import React, { useState, useRef, useEffect } from "react";
import {
  Home as HomeIcon, ShoppingBag, MessageCircle, User, Search, MapPin,
  ChevronRight, Star, Shield, Clock, ArrowLeft, SlidersHorizontal,
  Wind, Sparkles, Wrench, Scissors, Zap, Shirt, Check,
  Heart, Phone, Navigation, CreditCard,
  ThumbsUp, Award, Bell, Paintbrush, Hammer, Bug,
  Snowflake, X, Plus, Minus, Tag, Zap as ZapIcon, ChevronDown,
  CheckCircle, AlertCircle, MessageSquare, Camera,
} from "lucide-react";

/* ─── Styles ─── */
const FONT_STYLES = `
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&display=swap');
.font-display { font-family: 'Bricolage Grotesque', sans-serif; letter-spacing: -0.025em; }
.font-body { font-family: 'Plus Jakarta Sans', system-ui, sans-serif; letter-spacing: -0.01em; }
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { scrollbar-width: none; -ms-overflow-style: none; }
.shadow-phone { box-shadow: 0 50px 100px -20px rgba(28,25,23,0.25), 0 30px 60px -30px rgba(28,25,23,0.3); }
.shadow-tile { box-shadow: 0 4px 16px -4px rgba(28,25,23,0.06); }
.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
.float { animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100%{transform:translateY(0);} 50%{transform:translateY(-6px);} }
.slide-up { animation: slideUp 0.4s cubic-bezier(0.22,1,0.36,1); }
@keyframes slideUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
.scale-in { animation: scaleIn 0.35s cubic-bezier(0.22,1,0.36,1); }
@keyframes scaleIn { from { opacity:0; transform:scale(0.9); } to { opacity:1; transform:scale(1); } }
.slide-sheet { animation: slideSheet 0.4s cubic-bezier(0.22,1,0.36,1); }
@keyframes slideSheet { from { transform:translateY(100%); } to { transform:translateY(0); } }
.bounce-in { animation: bounceIn 0.55s cubic-bezier(0.22,1,0.36,1); }
@keyframes bounceIn { 0%{opacity:0;transform:scale(0.4)} 60%{transform:scale(1.12)} 80%{transform:scale(0.96)} 100%{opacity:1;transform:scale(1)} }
.spinner { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
.pulse-dot { animation: pulseDot 1.4s ease-in-out infinite; }
@keyframes pulseDot { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.5);opacity:0.6} }
.confetti-p { position:absolute; width:7px; height:7px; border-radius:1px; }
@keyframes confettiFall { 0%{opacity:1;transform:translateY(-12px) rotate(0deg)} 100%{opacity:0;transform:translateY(820px) rotate(680deg)} }
.bounce { animation: bounce 0.6s cubic-bezier(0.175,0.885,0.32,1.275); }
@keyframes bounce { 0%{transform:scale(0.3);opacity:0} 60%{transform:scale(1.1);opacity:1} 100%{transform:scale(1);opacity:1} }
@keyframes drivePro { 0%{left:6%} 100%{left:53%} }
.drive-pro { animation: drivePro 14s ease-out forwards; }
@keyframes pulsePing { 0%{transform:scale(1);opacity:0.8} 100%{transform:scale(2.5);opacity:0} }
.ping { animation: pulsePing 1.4s ease-out infinite; }
.shake { animation: shake 0.4s cubic-bezier(.36,.07,.19,.97) both; transform: translate3d(0, 0, 0); }
@keyframes shake { 10%, 90% { transform: translate3d(-1px, 0, 0); } 20%, 80% { transform: translate3d(2px, 0, 0); } 30%, 50%, 70% { transform: translate3d(-4px, 0, 0); } 40%, 60% { transform: translate3d(4px, 0, 0); } }
.pop { animation: pop 0.25s cubic-bezier(0.175,0.885,0.32,1.275); }
@keyframes pop { 0%{transform:scale(0.8);opacity:0} 100%{transform:scale(1);opacity:1} }
.glow-focus { transition: box-shadow 0.3s ease; }
.glow-focus:focus-within { box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.2); }
.bg-transition { transition: background-color 0.5s ease; }
.float-icon { animation: floatIcon 3s ease-in-out infinite; }
@keyframes floatIcon { 0%,100%{transform:translateY(0) scale(1);} 50%{transform:translateY(-8px) scale(1.05);} }
.radar-pulse { animation: radarPulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
@keyframes radarPulse { 0%{transform:scale(1);opacity:0.8} 100%{transform:scale(3);opacity:0} }
`;

/* ─── Services ─── */
const SERVICES = [
  { id:"ac",        name:"AC Service",   Icon:Wind,       gradient:"from-sky-100 to-sky-50",        iconBg:"bg-sky-500",     tag:"25% off", dotColor:"bg-sky-300",     category:"Cooling & Comfort" },
  { id:"cleaning",  name:"Cleaning",     Icon:Sparkles,   gradient:"from-emerald-100 to-emerald-50", iconBg:"bg-emerald-500", tag:"Popular", dotColor:"bg-emerald-300", category:"Home Care" },
  { id:"salon",     name:"Salon",        Icon:Scissors,   gradient:"from-rose-100 to-rose-50",       iconBg:"bg-rose-500",    tag:"New",     dotColor:"bg-rose-300",    category:"Beauty" },
  { id:"plumber",   name:"Plumber",      Icon:Wrench,     gradient:"from-amber-100 to-amber-50",     iconBg:"bg-amber-500",                  dotColor:"bg-amber-300",   category:"Repairs" },
  { id:"electric",  name:"Electrician",  Icon:Zap,        gradient:"from-violet-100 to-violet-50",   iconBg:"bg-violet-500",                 dotColor:"bg-violet-300",  category:"Repairs" },
  { id:"laundry",   name:"Laundry",      Icon:Shirt,      gradient:"from-teal-100 to-teal-50",       iconBg:"bg-teal-500",                   dotColor:"bg-teal-300",    category:"Home Care" },
  { id:"paint",     name:"Painting",     Icon:Paintbrush, gradient:"from-fuchsia-100 to-fuchsia-50", iconBg:"bg-fuchsia-500",                dotColor:"bg-fuchsia-300", category:"Home Improvement" },
  { id:"carpenter", name:"Carpenter",    Icon:Hammer,     gradient:"from-orange-100 to-orange-50",   iconBg:"bg-orange-500",                 dotColor:"bg-orange-300",  category:"Home Improvement" },
  { id:"pest",      name:"Pest Control", Icon:Bug,        gradient:"from-lime-100 to-lime-50",       iconBg:"bg-lime-600",                   dotColor:"bg-lime-300",    category:"Home Care" },
];

/* ─── Per-service pricing plans ─── */
const SERVICE_PLANS = {
  ac:        [
    { id:0, name:"Basic Clean",   price:399,  time:"30 min",     desc:"Filter clean + basic safety check" },
    { id:1, name:"Deep Service",  price:699,  time:"60 min",     desc:"Full jet wash + gas top-up + 30d warranty", popular:true },
    { id:2, name:"Annual AMC",    price:2999, time:"4 visits/yr",desc:"Quarterly care + priority support + parts" },
  ],
  cleaning:  [
    { id:0, name:"Standard",      price:599,  time:"1–1.5 hrs",  desc:"Sweep, mop, kitchen & bathroom wipe" },
    { id:1, name:"Deep Clean",    price:1199, time:"2–3 hrs",    desc:"Full scrub + appliances + sofa vacuum", popular:true },
    { id:2, name:"Move In/Out",   price:2499, time:"4–5 hrs",    desc:"Complete property handover clean" },
  ],
  salon:     [
    { id:0, name:"Express",       price:399,  time:"30 min",     desc:"Haircut + blow dry" },
    { id:1, name:"Pamper",        price:999,  time:"90 min",     desc:"Haircut + facial + head massage", popular:true },
    { id:2, name:"Bridal",        price:4999, time:"4 hrs",      desc:"Full bridal makeup + saree drape" },
  ],
  plumber:   [
    { id:0, name:"Checkup",       price:199,  time:"15 min",     desc:"Inspection + report" },
    { id:1, name:"Repair",        price:499,  time:"60 min",     desc:"Fix leaks, clogs & pressure issues", popular:true },
    { id:2, name:"Full Fitment",  price:999,  time:"2 hrs",      desc:"New tap / shower / pipeline install" },
  ],
  electric:  [
    { id:0, name:"Minor Fix",     price:149,  time:"20 min",     desc:"Bulb / switch / socket replacement" },
    { id:1, name:"Wiring Repair", price:599,  time:"60 min",     desc:"Fault detection + MCB + fan wiring", popular:true },
    { id:2, name:"Full Install",  price:1199, time:"2 hrs",      desc:"New panel / AC wiring / inverter" },
  ],
  laundry:   [
    { id:0, name:"Wash & Fold",   price:299,  time:"48 hrs",     desc:"Up to 5 kg regular laundry" },
    { id:1, name:"Premium",       price:699,  time:"24 hrs",     desc:"Dry clean + steam press", popular:true },
    { id:2, name:"Express",       price:999,  time:"6 hrs",      desc:"Same-day priority service" },
  ],
  paint:     [
    { id:0, name:"Touch-up",      price:1499, time:"1 day",      desc:"Single wall or patch repair" },
    { id:1, name:"Classic Room",  price:4999, time:"3 days",     desc:"Full room painting, 2 coats", popular:true },
    { id:2, name:"Royal Finish",  price:12999,time:"7 days",     desc:"Textured walls + premium paint" },
  ],
  carpenter: [
    { id:0, name:"Fix-it",        price:249,  time:"30 min",     desc:"Handle, hinge or lock repair" },
    { id:1, name:"Assembly",      price:899,  time:"90 min",     desc:"Bed / wardrobe / table setup", popular:true },
    { id:2, name:"Custom Work",   price:2499, time:"5 hrs",      desc:"New shelving or furniture mod" },
  ],
  pest:      [
    { id:0, name:"General",       price:699,  time:"45 min",     desc:"Cockroach + ant treatment" },
    { id:1, name:"Advanced",      price:1299, time:"90 min",     desc:"Herbal gel + rat control", popular:true },
    { id:2, name:"Full Home",     price:2499, time:"2.5 hrs",    desc:"Rodent + termite + bed bugs" },
  ],
};

/* ─── Per-service add-ons ─── */
const SERVICE_ADDONS = {
  ac:        [{ id:"foam",    label:"Foam Jet Deep Clean", price:199, emoji:"💨" },
              { id:"copper",  label:"Copper Coil Polish",  price:149, emoji:"🔧" },
              { id:"stab",    label:"Stabiliser Check",    price:99,  emoji:"⚡" }],
  cleaning:  [{ id:"sofa",   label:"Sofa Deep Clean",     price:299, emoji:"🛋" },
              { id:"carpet",  label:"Carpet Shampooing",   price:249, emoji:"🧹" },
              { id:"glass",   label:"Glass & Mirror Shine",price:149, emoji:"🪟" }],
  salon:     [{ id:"wax",    label:"Full Arms Waxing",    price:199, emoji:"✨" },
              { id:"mask",    label:"Hair Mask",           price:149, emoji:"💆" },
              { id:"manicure",label:"Gel Manicure",        price:349, emoji:"💅" }],
  plumber:   [{ id:"pipe",   label:"Pipe Insulation",     price:149, emoji:"🔩" },
              { id:"valve",   label:"Ball Valve Replace",  price:199, emoji:"🚰" },
              { id:"drain",   label:"Floor Drain Clean",   price:99,  emoji:"🕳" }],
  electric:  [{ id:"surge",  label:"Surge Protector Fit", price:199, emoji:"🔋" },
              { id:"earthing",label:"Earthing Check",      price:149, emoji:"🛡" },
              { id:"panel",   label:"Panel Labelling",     price:99,  emoji:"🏷" }],
  laundry:   [{ id:"stain",  label:"Stain Treatment",     price:99,  emoji:"🧴" },
              { id:"iron",    label:"Steam Iron Press",    price:79,  emoji:"👔" },
              { id:"fold",    label:"Wardrobe Fold & Set", price:149, emoji:"📦" }],
  paint:     [{ id:"putty",  label:"Wall Putty Finish",   price:499, emoji:"🪣" },
              { id:"primer",  label:"Anti-fungal Primer",  price:399, emoji:"🛡" },
              { id:"texture", label:"Texture Coat Wall",   price:799, emoji:"🎨" }],
  carpenter: [{ id:"polish", label:"Wood Polish",         price:199, emoji:"✨" },
              { id:"rubber",  label:"Anti-scratch Pads",   price:99,  emoji:"🟤" },
              { id:"handle",  label:"Designer Handles",    price:249, emoji:"🚪" }],
  pest:      [{ id:"herbal", label:"Herbal Formula",      price:199, emoji:"🌿" },
              { id:"rats",    label:"Rat Trap Setup",      price:149, emoji:"🐭" },
              { id:"net",     label:"Window Net Fitting",  price:299, emoji:"🕸" }],
};

/* ─── Service meta (description, rating, includes) ─── */
const SERVICE_META = {
  ac:        { color:"sky",     time:"30–60 min", rating:4.9, reviews:"18.4k",
               includes:["Filter cleaning & deodorising","Indoor unit deep clean","Gas pressure check","Outdoor unit wash","30-day service warranty"] },
  cleaning:  { color:"emerald", time:"60–90 min", rating:4.8, reviews:"22.1k",
               includes:["Full home sweep & mop","Kitchen scrub down","Bathroom deep clean","Dusting & fan cleaning","Garbage disposal"] },
  salon:     { color:"rose",    time:"45–75 min", rating:4.9, reviews:"9.3k",
               includes:["Haircut & styling","Facial or cleanup","Eyebrow threading","Head massage","Premium products used"] },
  plumber:   { color:"amber",   time:"30–60 min", rating:4.7, reviews:"11.2k",
               includes:["Leak detection & fix","Tap & shower repair","Pipe unclogging","Water pressure check","30-day guarantee"] },
  electric:  { color:"violet",  time:"30–60 min", rating:4.8, reviews:"13.6k",
               includes:["Switch & socket repair","Fan & light fitting","Short circuit diagnosis","MCB/fuse replacement","Safety check"] },
  laundry:   { color:"teal",    time:"24–48 hr",  rating:4.7, reviews:"7.8k",
               includes:["Wash & fold","Dry cleaning","Steam press","Stain treatment","Same-day pickup"] },
  paint:     { color:"fuchsia", time:"2–5 days",  rating:4.8, reviews:"6.1k",
               includes:["Wall prep & putty","Premium paint application","2 coats minimum","Clean-up after work","1-year warranty"] },
  carpenter: { color:"orange",  time:"60–120 min",rating:4.7, reviews:"8.4k",
               includes:["Furniture assembly","Door/window repair","Custom shelving","Lock fitting","Wood polish"] },
  pest:      { color:"lime",    time:"60–90 min", rating:4.8, reviews:"10.2k",
               includes:["Cockroach treatment","Rat/rodent control","Termite inspection","Bed bug treatment","3-month guarantee"] },
};

/* ─── Related services ("others also booked") ─── */
const RELATED = {
  ac:"electric,pest",    cleaning:"pest,laundry",  salon:"laundry,cleaning",
  plumber:"electric,carpenter", electric:"plumber,carpenter", laundry:"cleaning,salon",
  paint:"carpenter,cleaning",   carpenter:"paint,electric",   pest:"cleaning,laundry",
};

/* ─── Safety / trust badges (UrbanCompany style) ─── */
const SAFETY = [
  { emoji:"🛡", label:"ID Verified" }, { emoji:"🧤", label:"Gloves worn" },
  { emoji:"🧪", label:"Sanitised kit" }, { emoji:"💰", label:"Fixed price" },
  { emoji:"⭐", label:"Rated 4.8+" },  { emoji:"🔒", label:"Insured" },
];

/* ─── Promo codes ─── */
const COUPONS = { WELCOMEHOME:100, AGAK50:50, FIRSTBOOK:150, AGAKPLUS:200 };

/* ─── Deterministic confetti (no Math.random → no flicker) ─── */
const CONFETTI = (() => {
  const colors = ["bg-orange-500","bg-emerald-500","bg-violet-500","bg-amber-400","bg-rose-500","bg-sky-500","bg-teal-500"];
  return Array.from({ length:28 }, (_,i) => ({
    left:`${(i*3.7+1.5)%94}%`,
    delay:`${(i*0.07).toFixed(2)}s`,
    color: colors[i % colors.length],
    round: i%3===0,
    dur:`${0.9+(i%5)*0.08}s`,
  }));
})();

/* ─── Techs ─── */
const TECHS = [
  { initials:"RP", name:"Ramesh Patel",  role:"AC Specialist",  rating:4.9, jobs:"2.3k", color:"from-orange-500 to-orange-700",  years:12, languages:"Hindi · Gujarati", svcIds:["ac","electric"] },
  { initials:"SM", name:"Suresh Mehta",  role:"Deep Cleaner",   rating:4.8, jobs:"1.2k", color:"from-emerald-500 to-emerald-700", years:8,  languages:"Hindi · Gujarati", svcIds:["cleaning","laundry","pest"] },
  { initials:"PS", name:"Priya Sharma",  role:"Salon Pro",      rating:5.0, jobs:"892",  color:"from-rose-500 to-rose-700",       years:6,  languages:"Hindi · English",  svcIds:["salon"] },
  { initials:"VK", name:"Vijay Kadam",   role:"Plumber",        rating:4.7, jobs:"654",  color:"from-amber-500 to-amber-700",     years:15, languages:"Gujarati",         svcIds:["plumber","carpenter"] },
  { initials:"NK", name:"Nikhil Khatri", role:"Painter",        rating:4.9, jobs:"431",  color:"from-fuchsia-500 to-fuchsia-700", years:10, languages:"Hindi · Gujarati", svcIds:["paint","carpenter"] },
];

const getTech = (svcId) => TECHS.find(t => t.svcIds.includes(svcId)) || TECHS[0];

/* ══════════════════════════════════════════════════════════
   OVERLAY COMPONENTS
══════════════════════════════════════════════════════════ */

/* Confetti rain */
function ConfettiOverlay() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-50">
      {CONFETTI.map((c,i) => (
        <div key={i} className={`confetti-p ${c.color} ${c.round?"rounded-full":""}`}
          style={{ left:c.left, top:0, animationName:"confettiFall", animationDuration:c.dur, animationDelay:c.delay, animationFillMode:"forwards" }} />
      ))}
    </div>
  );
}

/* Payment processing → success popup */
function PaymentPopup({ total, state, onPhase, onDone }) {
  useEffect(() => {
    if (state === "processing") {
      const t = setTimeout(() => onPhase("success"), 1800);
      return () => clearTimeout(t);
    }
    if (state === "success") {
      const t = setTimeout(() => onDone(), 2500);
      return () => clearTimeout(t);
    }
  }, [state]);

  return (
    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
      {state === "success" && <ConfettiOverlay />}
      <div className={`bg-white rounded-3xl p-8 mx-6 text-center shadow-2xl ${state==="success"?"bounce-in":"scale-in"}`}>
        {state === "processing" ? (
          <>
            <div className="w-16 h-16 border-4 border-orange-200 border-t-orange-500 rounded-full spinner mx-auto mb-4" />
            <p className="font-bold text-stone-800 text-lg">Processing payment…</p>
            <p className="text-stone-400 text-sm mt-1">₹{total.toLocaleString("en-IN")}</p>
          </>
        ) : (
          <>
            <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="text-emerald-500" size={40} strokeWidth={3} />
            </div>
            <p className="font-display font-bold text-stone-900 text-2xl">Payment Done! 🎉</p>
            <p className="text-stone-500 text-sm mt-2">₹{total.toLocaleString("en-IN")} paid successfully</p>
            <p className="text-emerald-600 text-xs font-semibold mt-3 bg-emerald-50 rounded-xl py-2 px-4">
              Booking confirmed · Pro assigned shortly
            </p>
          </>
        )}
      </div>
    </div>
  );
}

/* Booking confirmed popup (non-payment) */
function BookingConfirmPopup({ onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2400);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
      <ConfettiOverlay />
      <div className="bg-white rounded-3xl p-8 mx-6 text-center shadow-2xl bounce-in">
        <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="text-emerald-500" size={40} strokeWidth={3} />
        </div>
        <p className="font-display font-bold text-stone-900 text-2xl">Booking Done! 🎊</p>
        <p className="text-stone-500 text-sm mt-2">Your pro is on their way soon</p>
      </div>
    </div>
  );
}

/* Quick Book bottom sheet (Snabbit-style nearby pros) */
function QuickBookSheet({ svc, plan, onClose, goTo }) {
  const [booked, setBooked] = useState(false);
  const nearbyPros = [
    { initials:"RP", name:"Ramesh P.",  dist:"0.8 km", eta:"12 min", rating:4.9, price:plan?.price || 399 },
    { initials:"AK", name:"Arvind K.", dist:"1.2 km", eta:"18 min", rating:4.8, price:(plan?.price || 399)+50 },
    { initials:"MV", name:"Manish V.", dist:"2.1 km", eta:"25 min", rating:4.7, price:(plan?.price || 399)+20 },
  ];
  const handleBook = () => {
    setBooked(true);
    setTimeout(() => { onClose(); goTo("tracking"); }, 1800);
  };
  return (
    <div className="absolute inset-0 bg-black/50 z-40 flex items-end">
      <div className="w-full bg-white rounded-t-3xl slide-sheet pb-6">
        {booked ? (
          <div className="p-8 text-center">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3 bounce-in">
              <Check className="text-emerald-500" size={32} strokeWidth={3} />
            </div>
            <p className="font-bold text-stone-900 text-lg">Pro assigned! 🚀</p>
            <p className="text-stone-500 text-sm mt-1">Opening live tracking…</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between px-5 pt-5 pb-3">
              <div>
                <p className="font-bold text-stone-900">⚡ Quick Book</p>
                <p className="text-xs text-stone-500">{svc?.name} — pros near you right now</p>
              </div>
              <button onClick={onClose} className="w-8 h-8 bg-stone-100 rounded-full flex items-center justify-center">
                <X size={16} className="text-stone-500" />
              </button>
            </div>
            <div className="space-y-2 px-4">
              {nearbyPros.map((p, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-2xl border border-stone-100 bg-stone-50">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">{p.initials}</div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-stone-800 text-sm">{p.name}</p>
                    <p className="text-xs text-stone-500">⭐ {p.rating} · 📍 {p.dist} · ETA {p.eta}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-stone-900">₹{p.price}</p>
                    <button onClick={handleBook}
                      className="text-xs bg-orange-500 text-white px-3 py-1 rounded-full font-semibold mt-1">
                      Book
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* Rating sheet */
function RatingSheet({ svc, tech, onClose }) {
  const [stars, setStars]     = useState(0);
  const [hover, setHover]     = useState(0);
  const [tags, setTags]       = useState(new Set());
  const [done, setDone]       = useState(false);
  const TAGS = ["On time","Very polite","Clean work","Explained well","Great quality","Would rebook"];
  const toggleTag = t => setTags(prev => { const s=new Set(prev); s.has(t)?s.delete(t):s.add(t); return s; });
  const submit = () => { setDone(true); setTimeout(onClose, 1800); };
  return (
    <div className="absolute inset-0 bg-black/50 z-40 flex items-end">
      <div className="w-full bg-white rounded-t-3xl slide-sheet pb-8">
        {done ? (
          <div className="p-8 text-center bounce-in">
            <div className="text-4xl mb-3">🙏</div>
            <p className="font-bold text-stone-900 text-lg">Thanks for rating!</p>
            <p className="text-stone-500 text-sm mt-1">Your feedback helps pros improve</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between px-5 pt-5 pb-4">
              <p className="font-bold text-stone-900">Rate your experience</p>
              <button onClick={onClose} className="w-8 h-8 bg-stone-100 rounded-full flex items-center justify-center">
                <X size={16} className="text-stone-500" />
              </button>
            </div>
            <div className="text-center px-5">
              <div className="flex items-center gap-3 mb-4 bg-stone-50 rounded-2xl p-3">
                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${tech.color} flex items-center justify-center text-white font-bold`}>{tech.initials}</div>
                <div className="text-left">
                  <p className="font-semibold text-stone-800">{tech.name}</p>
                  <p className="text-xs text-stone-500">{svc?.name || "Home Service"}</p>
                </div>
              </div>
              <div className="flex justify-center gap-2 mb-4">
                {[1,2,3,4,5].map(n => (
                  <button key={n} onMouseEnter={()=>setHover(n)} onMouseLeave={()=>setHover(0)} onClick={()=>setStars(n)}>
                    <Star size={32} className={`transition-all ${(hover||stars)>=n?"text-amber-400 fill-amber-400":"text-stone-200"}`} />
                  </button>
                ))}
              </div>
              {stars > 0 && (
                <div className="fade-in">
                  <p className="text-sm text-stone-500 mb-3">What went well?</p>
                  <div className="flex flex-wrap gap-2 justify-center mb-4">
                    {TAGS.map(t => (
                      <button key={t} onClick={()=>toggleTag(t)}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${tags.has(t)?"bg-orange-500 text-white border-orange-500":"bg-stone-50 text-stone-600 border-stone-200"}`}>
                        {t}
                      </button>
                    ))}
                  </div>
                  <button onClick={submit}
                    className="w-full bg-orange-500 text-white rounded-2xl py-3 font-bold text-sm">
                    Submit Rating
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   SCREENS
══════════════════════════════════════════════════════════ */

function SplashScreen() {
  return (
    <div className="absolute inset-0 bg-gradient-to-br from-orange-500 via-orange-400 to-amber-400 flex flex-col items-center justify-center">
      <div className="float text-center">
        <div className="w-20 h-20 bg-white/20 rounded-3xl flex items-center justify-center mb-5 mx-auto border border-white/30 backdrop-blur-sm">
          <Snowflake size={40} className="text-white" strokeWidth={1.5} />
        </div>
        <p className="font-display text-white text-4xl font-bold tracking-tight">agak</p>
        <p className="text-orange-100 text-sm mt-2 font-medium">Home services, sorted.</p>
      </div>
      <div className="absolute bottom-12 flex gap-1.5">
        {[0,1,2].map(i=><div key={i} className={`h-1.5 rounded-full bg-white ${i===0?"w-6 opacity-100":"w-1.5 opacity-40"}`}/>)}
      </div>
    </div>
  );
}

function HomeScreen({ goTo, openService, user }) {
  const [searchQ, setSearchQ] = useState("");
  const filteredServices = SERVICES.filter(s =>
    s.name.toLowerCase().includes(searchQ.toLowerCase()) ||
    s.category.toLowerCase().includes(searchQ.toLowerCase())
  );

  return (
    <div className="absolute inset-0 bg-stone-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white px-5 pt-10 pb-4 flex-shrink-0">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-1.5 text-stone-500 text-xs font-medium mb-1">
              <MapPin size={12} className="text-orange-500" />
              <span>{user?.location || "Rajkot, Gujarat"}</span>
              <ChevronDown size={12} />
            </div>
            <p className="font-display text-stone-900 text-2xl font-bold leading-tight">Good morning,<br/>{(user?.name || "Akash").split(' ')[0]}! 👋</p>
          </div>
          <div className="flex gap-2">
            <button className="w-9 h-9 bg-stone-100 rounded-full flex items-center justify-center relative">
              <Bell size={18} className="text-stone-600" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-orange-500 rounded-full" />
            </button>
          </div>
        </div>

        {/* Search bar */}
        <div className="flex items-center gap-3 bg-stone-100 rounded-2xl px-4 py-3">
          <Search size={16} className="text-stone-400" />
          <input value={searchQ} onChange={e=>setSearchQ(e.target.value)}
            className="flex-1 bg-transparent text-sm text-stone-700 placeholder-stone-400 outline-none font-medium"
            placeholder="Search AC service, cleaning…" />
          {searchQ && <button onClick={()=>setSearchQ("")}><X size={14} className="text-stone-400" /></button>}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar">
        {/* Quick Book strip */}
        <div className="mx-4 mt-4 bg-gradient-to-r from-orange-500 to-amber-500 rounded-2xl p-4 flex items-center gap-3"
          onClick={()=>openService(SERVICES[0])}>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 bg-white rounded-full pulse-dot" />
              <p className="text-white text-xs font-bold uppercase tracking-wide">Pros online near you</p>
            </div>
            <p className="text-white font-display font-bold text-lg leading-tight">Book in 60 seconds ⚡</p>
            <p className="text-orange-100 text-xs mt-0.5">8 pros available · Rajkot area</p>
          </div>
          <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center">
            <Zap size={24} className="text-white" />
          </div>
        </div>

        {/* Promo banner */}
        <div className="mx-4 mt-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-2xl p-4">
          <p className="text-violet-200 text-xs font-semibold">LIMITED TIME</p>
          <p className="text-white font-display font-bold text-lg">₹200 off your first booking</p>
          <p className="text-violet-200 text-sm">Use code <span className="text-white font-bold">FIRSTBOOK</span></p>
        </div>

        {/* Categories */}
        <div className="px-5 mt-5 mb-3 flex items-center justify-between">
          <p className="font-bold text-stone-900 text-base">What do you need?</p>
          <button className="text-xs text-orange-500 font-bold">See all</button>
        </div>

        {/* Service grid */}
        <div className="px-4 grid grid-cols-3 gap-3 pb-2">
          {(searchQ ? filteredServices : SERVICES).map(svc => (
            <button key={svc.id} onClick={()=>openService(svc)}
              className={`relative bg-gradient-to-b ${svc.gradient} rounded-2xl p-3 text-left shadow-tile active:scale-95 transition-transform`}>
              {svc.tag && (
                <span className="absolute top-2 right-2 text-[9px] font-bold bg-orange-500 text-white px-1.5 py-0.5 rounded-full">{svc.tag}</span>
              )}
              <div className={`w-10 h-10 ${svc.iconBg} rounded-xl flex items-center justify-center mb-2`}>
                <svc.Icon size={20} className="text-white" />
              </div>
              <p className="text-stone-800 font-semibold text-xs leading-tight">{svc.name}</p>
              <p className="text-stone-400 text-[10px] mt-0.5">{svc.category}</p>
            </button>
          ))}
        </div>

        {/* Top pros */}
        <div className="px-5 mt-5 mb-3">
          <p className="font-bold text-stone-900 text-base">Top rated pros</p>
        </div>
        <div className="flex gap-3 px-4 overflow-x-auto no-scrollbar pb-2">
          {TECHS.map((t,i) => (
            <div key={i} className="flex-shrink-0 w-36 bg-white rounded-2xl p-3 shadow-tile">
              <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${t.color} flex items-center justify-center text-white font-bold text-sm mb-2`}>{t.initials}</div>
              <p className="font-semibold text-stone-800 text-xs">{t.name}</p>
              <p className="text-stone-400 text-[10px]">{t.role}</p>
              <div className="flex items-center gap-1 mt-1.5">
                <Star size={10} className="text-amber-400 fill-amber-400" />
                <span className="text-stone-700 text-[10px] font-bold">{t.rating}</span>
                <span className="text-stone-400 text-[10px]">· {t.jobs} jobs</span>
              </div>
            </div>
          ))}
        </div>

        <div className="h-24" />
      </div>
    </div>
  );
}

function ServiceScreen({ svc, goTo, setQuickBk }) {
  const meta    = SERVICE_META[svc.id] || SERVICE_META.ac;
  const plans   = SERVICE_PLANS[svc.id] || SERVICE_PLANS.ac;
  const addons  = SERVICE_ADDONS[svc.id] || [];
  const tech    = getTech(svc.id);
  const related = (RELATED[svc.id]||"").split(",").map(id=>SERVICES.find(s=>s.id===id)).filter(Boolean);

  const [selectedPlan, setPlan] = useState(1);
  const [liked, setLiked]       = useState(false);
  const colorMap = { sky:"text-sky-500", emerald:"text-emerald-500", rose:"text-rose-500", amber:"text-amber-500", violet:"text-violet-500", teal:"text-teal-500", fuchsia:"text-fuchsia-500", orange:"text-orange-500", lime:"text-lime-500" };
  const bgMap    = { sky:"bg-sky-500", emerald:"bg-emerald-500", rose:"bg-rose-500", amber:"bg-amber-500", violet:"bg-violet-500", teal:"bg-teal-500", fuchsia:"bg-fuchsia-500", orange:"bg-orange-500", lime:"bg-lime-600" };

  return (
    <div className="absolute inset-0 bg-white flex flex-col overflow-hidden">
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto no-scrollbar">
        {/* Hero */}
        <div className={`bg-gradient-to-b ${svc.gradient} px-5 pt-12 pb-5`}>
          <div className="flex items-center justify-between mb-4">
            <button onClick={()=>goTo("home","home")} className="w-9 h-9 bg-white/80 backdrop-blur rounded-full flex items-center justify-center shadow-sm">
              <ArrowLeft size={18} className="text-stone-700" />
            </button>
            <button onClick={()=>setLiked(l=>!l)} className="w-9 h-9 bg-white/80 backdrop-blur rounded-full flex items-center justify-center shadow-sm">
              <Heart size={18} className={liked?"text-rose-500 fill-rose-500":"text-stone-500"} />
            </button>
          </div>
          <div className="flex items-center gap-4">
            <div className={`w-16 h-16 ${svc.iconBg} rounded-2xl flex items-center justify-center shadow-lg`}>
              <svc.Icon size={32} className="text-white" />
            </div>
            <div>
              <p className="font-display font-bold text-stone-900 text-2xl">{svc.name}</p>
              <div className="flex items-center gap-3 mt-1">
                <span className="flex items-center gap-1 text-sm font-semibold text-amber-500">
                  <Star size={13} className="fill-amber-400" /> {meta.rating}
                </span>
                <span className="text-stone-400 text-xs">({meta.reviews} reviews)</span>
                <span className="flex items-center gap-1 text-stone-500 text-xs">
                  <Clock size={11} /> {meta.time}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Safety badges */}
        <div className="px-4 py-3 border-b border-stone-100">
          <div className="flex gap-2 overflow-x-auto no-scrollbar">
            {SAFETY.map((s,i) => (
              <div key={i} className="flex-shrink-0 flex items-center gap-1.5 bg-stone-50 rounded-xl px-3 py-1.5">
                <span className="text-sm">{s.emoji}</span>
                <span className="text-xs text-stone-600 font-medium whitespace-nowrap">{s.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Plans */}
        <div className="px-4 pt-4">
          <p className="font-bold text-stone-900 mb-3">Choose a plan</p>
          <div className="space-y-2">
            {plans.map((p, i) => (
              <button key={i} onClick={()=>setPlan(i)}
                className={`w-full flex items-center gap-3 p-3.5 rounded-2xl border-2 text-left transition-all ${selectedPlan===i?"border-orange-500 bg-orange-50":"border-stone-100 bg-stone-50"}`}>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${selectedPlan===i?"border-orange-500 bg-orange-500":"border-stone-300"}`}>
                  {selectedPlan===i && <Check size={10} className="text-white" strokeWidth={3} />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-stone-900 text-sm">{p.name}</span>
                    {p.popular && <span className="text-[9px] font-bold bg-orange-500 text-white px-1.5 py-0.5 rounded-full">POPULAR</span>}
                  </div>
                  <p className="text-stone-500 text-xs mt-0.5">{p.desc}</p>
                  <p className="text-stone-400 text-[10px] mt-0.5">⏱ {p.time}</p>
                </div>
                <p className="font-display font-bold text-stone-900 text-base flex-shrink-0">₹{p.price}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Add-ons */}
        {addons.length > 0 && (
          <div className="px-4 pt-4">
            <p className="font-bold text-stone-900 mb-3">Enhance your service</p>
            <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1">
              {addons.map(a => (
                <div key={a.id} className="flex-shrink-0 bg-stone-50 border border-stone-100 rounded-2xl p-3 text-center w-24">
                  <span className="text-2xl">{a.emoji}</span>
                  <p className="text-stone-700 text-[10px] font-semibold mt-1 leading-tight">{a.label}</p>
                  <p className="text-orange-500 text-xs font-bold mt-1">+₹{a.price}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* How it works */}
        <div className="px-4 pt-4">
          <p className="font-bold text-stone-900 mb-3">How it works</p>
          <div className="flex gap-3">
            {["Book online","Pro assigned","Service done","Pay & rate"].map((step, i) => (
              <div key={i} className="flex-1 text-center">
                <div className="w-9 h-9 bg-orange-100 rounded-xl flex items-center justify-center mx-auto mb-1.5">
                  <span className="text-orange-600 font-bold text-sm">{i+1}</span>
                </div>
                <p className="text-stone-600 text-[10px] font-medium leading-tight">{step}</p>
              </div>
            ))}
          </div>
        </div>

        {/* What's included */}
        <div className="px-4 pt-4">
          <p className="font-bold text-stone-900 mb-3">What's included</p>
          <div className="space-y-2">
            {meta.includes.map((item, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <div className={`w-5 h-5 ${bgMap[meta.color]||"bg-orange-500"} rounded-full flex items-center justify-center flex-shrink-0 mt-0.5`}>
                  <Check size={10} className="text-white" strokeWidth={3} />
                </div>
                <p className="text-stone-600 text-sm">{item}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Assigned tech */}
        <div className="mx-4 mt-4 bg-stone-50 rounded-2xl p-4">
          <p className="font-bold text-stone-900 mb-3 text-sm">Your pro</p>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${tech.color} flex items-center justify-center text-white font-bold`}>{tech.initials}</div>
            <div className="flex-1">
              <p className="font-semibold text-stone-800">{tech.name}</p>
              <p className="text-stone-500 text-xs">{tech.role} · {tech.years} yrs exp</p>
              <div className="flex items-center gap-1 mt-0.5">
                <Star size={11} className="text-amber-400 fill-amber-400" />
                <span className="text-stone-700 text-xs font-bold">{tech.rating}</span>
                <span className="text-stone-400 text-xs">· {tech.jobs} jobs</span>
              </div>
            </div>
            <div className="flex gap-2">
              <button className="w-9 h-9 bg-white border border-stone-200 rounded-full flex items-center justify-center">
                <Phone size={14} className="text-stone-600" />
              </button>
              <button className="w-9 h-9 bg-white border border-stone-200 rounded-full flex items-center justify-center">
                <MessageSquare size={14} className="text-stone-600" />
              </button>
            </div>
          </div>
        </div>

        {/* Others also booked */}
        {related.length > 0 && (
          <div className="px-4 pt-4">
            <p className="font-bold text-stone-900 mb-3 text-sm">Others also booked</p>
            <div className="flex gap-3">
              {related.map(r => (
                <button key={r.id} onClick={()=>{ setPlan(1); goTo("service"); /* re-open with new svc */ }}
                  className={`flex-1 bg-gradient-to-b ${r.gradient} rounded-2xl p-3 text-center shadow-tile`}>
                  <div className={`w-10 h-10 ${r.iconBg} rounded-xl flex items-center justify-center mx-auto mb-2`}>
                    <r.Icon size={20} className="text-white" />
                  </div>
                  <p className="text-stone-800 font-semibold text-xs">{r.name}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="h-32" />
      </div>

      {/* Bottom actions */}
      <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-stone-100 px-4 py-4 flex gap-3">
        <button onClick={()=>setQuickBk(true)}
          className="flex-none px-4 py-3 bg-amber-100 text-amber-700 rounded-2xl font-bold text-sm flex items-center gap-1.5">
          <Zap size={16} /> Quick
        </button>
        <button onClick={()=>goTo("booking")}
          className="flex-1 bg-orange-500 text-white rounded-2xl py-3 font-bold text-sm flex items-center justify-center gap-2">
          Book ₹{plans[selectedPlan]?.price || plans[1].price}
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

function BookingScreen({ svc, goTo, onPay, user, setUser }) {
  const plans    = SERVICE_PLANS[svc.id] || SERVICE_PLANS.ac;
  const addons   = SERVICE_ADDONS[svc.id] || [];
  const [plan, setPlan]     = useState(1);
  const [picked, setPicked] = useState(new Set());
  const [coupon, setCoupon] = useState("");
  const [couponOk, setCouponOk] = useState(false);
  const [couponErr, setCouponErr] = useState("");
  const [slot, setSlot]     = useState({ day:"Tomorrow", time:"11 AM – 1 PM" });

  const toggleAddon = id => setPicked(prev => { const s=new Set(prev); s.has(id)?s.delete(id):s.add(id); return s; });
  const applyCoupon = () => {
    if (COUPONS[coupon.toUpperCase()]) { setCouponOk(true); setCouponErr(""); }
    else { setCouponOk(false); setCouponErr("Invalid code"); }
  };
  const discount   = couponOk ? (COUPONS[coupon.toUpperCase()]||0) : 0;
  const addonTotal = addons.filter(a=>picked.has(a.id)).reduce((s,a)=>s+a.price, 0);
  const base       = plans[plan]?.price || 0;
  const total      = base + addonTotal - discount;
  const DAYS       = ["Today","Tomorrow","Wed 14","Thu 15","Fri 16"];
  const TIMES      = ["8–10 AM","10–12 PM","11 AM–1 PM","2–4 PM","5–7 PM"];

  return (
    <div className="absolute inset-0 bg-stone-50 flex flex-col overflow-hidden">
      <div className="bg-white px-5 pt-10 pb-4 flex items-center gap-3 flex-shrink-0">
        <button onClick={()=>goTo("service")} className="w-9 h-9 bg-stone-100 rounded-full flex items-center justify-center">
          <ArrowLeft size={18} className="text-stone-700" />
        </button>
        <p className="font-display font-bold text-stone-900 text-xl">Book {svc.name}</p>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar">
        {/* Plan selector */}
        <div className="bg-white mx-4 mt-4 rounded-2xl p-4 shadow-tile">
          <p className="font-bold text-stone-900 text-sm mb-3">Selected plan</p>
          {plans.map((p,i) => (
            <button key={i} onClick={()=>setPlan(i)}
              className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 text-left mb-2 transition-all ${plan===i?"border-orange-500 bg-orange-50":"border-stone-100"}`}>
              <div className={`w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center ${plan===i?"border-orange-500 bg-orange-500":"border-stone-300"}`}>
                {plan===i && <Check size={8} className="text-white" strokeWidth={3} />}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-stone-800 text-sm">{p.name}</span>
                  {p.popular && <span className="text-[9px] font-bold bg-orange-500 text-white px-1.5 py-0.5 rounded-full">BEST</span>}
                </div>
                <p className="text-stone-400 text-xs">{p.time}</p>
              </div>
              <span className="font-bold text-stone-900 text-sm">₹{p.price}</span>
            </button>
          ))}
        </div>

        {/* Add-ons */}
        {addons.length > 0 && (
          <div className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-tile">
            <p className="font-bold text-stone-900 text-sm mb-3">Add-ons</p>
            <div className="space-y-2">
              {addons.map(a => (
                <button key={a.id} onClick={()=>toggleAddon(a.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${picked.has(a.id)?"border-orange-500 bg-orange-50":"border-stone-100"}`}>
                  <span className="text-xl">{a.emoji}</span>
                  <span className="flex-1 text-sm font-medium text-stone-700 text-left">{a.label}</span>
                  <span className={`text-sm font-bold ${picked.has(a.id)?"text-orange-500":"text-stone-500"}`}>+₹{a.price}</span>
                  <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${picked.has(a.id)?"border-orange-500 bg-orange-500":"border-stone-300"}`}>
                    {picked.has(a.id) && <Check size={10} className="text-white" strokeWidth={3} />}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Schedule */}
        <div className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-tile">
          <p className="font-bold text-stone-900 text-sm mb-3">📅 Choose date</p>
          <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1 mb-3">
            {DAYS.map(d => (
              <button key={d} onClick={()=>setSlot(s=>({...s,day:d}))}
                className={`flex-shrink-0 px-3 py-2 rounded-xl text-xs font-semibold border-2 ${slot.day===d?"border-orange-500 bg-orange-50 text-orange-600":"border-stone-100 text-stone-500"}`}>
                {d}
              </button>
            ))}
          </div>
          <p className="font-bold text-stone-900 text-sm mb-3">🕐 Choose time</p>
          <div className="flex gap-2 flex-wrap">
            {TIMES.map(t => (
              <button key={t} onClick={()=>setSlot(s=>({...s,time:t}))}
                className={`px-3 py-2 rounded-xl text-xs font-semibold border-2 ${slot.time===t?"border-orange-500 bg-orange-50 text-orange-600":"border-stone-100 text-stone-500"}`}>
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-tile">
          <p className="font-bold text-stone-900 text-sm mb-2">📍 Address</p>
          <div className="flex items-center gap-2 bg-stone-50 rounded-xl px-3 py-2.5">
            <MapPin size={14} className="text-orange-500 flex-shrink-0" />
            <input value={user?.address} onChange={e=>setUser && setUser(u=>({...u, address: e.target.value}))}
              className="flex-1 bg-transparent text-sm text-stone-700 outline-none" />
          </div>
        </div>

        {/* Coupon */}
        <div className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-tile">
          <p className="font-bold text-stone-900 text-sm mb-3">🏷 Promo code</p>
          <div className="flex gap-2">
            <div className={`flex-1 flex items-center gap-2 border-2 rounded-xl px-3 py-2.5 ${couponOk?"border-emerald-400 bg-emerald-50":couponErr?"border-red-300":"border-stone-200"}`}>
              <Tag size={14} className={couponOk?"text-emerald-500":"text-stone-400"} />
              <input value={coupon} onChange={e=>{setCoupon(e.target.value.toUpperCase());setCouponOk(false);setCouponErr("");}}
                className="flex-1 bg-transparent text-sm font-mono font-bold text-stone-700 placeholder-stone-300 outline-none"
                placeholder="WELCOMEHOME" maxLength={12} />
              {couponOk && <Check size={14} className="text-emerald-500" />}
            </div>
            <button onClick={applyCoupon}
              className="px-4 py-2.5 bg-stone-900 text-white rounded-xl text-sm font-bold">
              Apply
            </button>
          </div>
          {couponErr && <p className="text-red-500 text-xs mt-1.5 ml-1">{couponErr}</p>}
          {couponOk && <p className="text-emerald-600 text-xs mt-1.5 ml-1 font-semibold">✓ ₹{discount} discount applied!</p>}
          <div className="flex gap-2 mt-3 overflow-x-auto no-scrollbar">
            {Object.keys(COUPONS).map(c => (
              <button key={c} onClick={()=>{setCoupon(c);setCouponOk(false);setCouponErr("");}}
                className="flex-shrink-0 px-2.5 py-1 bg-orange-50 text-orange-600 border border-orange-200 rounded-lg text-[10px] font-bold">
                {c}
              </button>
            ))}
          </div>
        </div>

        {/* Bill summary */}
        <div className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-tile">
          <p className="font-bold text-stone-900 text-sm mb-3">Bill summary</p>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-stone-500">{plans[plan]?.name}</span>
              <span className="font-semibold text-stone-800">₹{base}</span>
            </div>
            {addons.filter(a=>picked.has(a.id)).map(a => (
              <div key={a.id} className="flex justify-between">
                <span className="text-stone-500">{a.emoji} {a.label}</span>
                <span className="font-semibold text-stone-800">+₹{a.price}</span>
              </div>
            ))}
            {discount > 0 && (
              <div className="flex justify-between text-emerald-600">
                <span>Coupon ({coupon})</span>
                <span className="font-semibold">−₹{discount}</span>
              </div>
            )}
            <div className="border-t border-stone-100 pt-2 flex justify-between">
              <span className="font-bold text-stone-900">Total</span>
              <span className="font-display font-bold text-stone-900 text-base">₹{total}</span>
            </div>
          </div>
        </div>

        <div className="h-28" />
      </div>

      {/* Pay button */}
      <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-stone-100 px-4 py-4">
        <button onClick={()=>onPay(total, plans[plan].name, slot.day)}
          className="w-full bg-orange-500 text-white rounded-2xl py-4 font-display font-bold text-base flex items-center justify-center gap-2">
          <CreditCard size={18} />
          Pay ₹{total.toLocaleString("en-IN")}
        </button>
      </div>
    </div>
  );
}

function ConfirmScreen({ svc, goTo, setRating }) {
  const [showConfetti, setShowConfetti] = useState(true);
  const tech = getTech(svc.id);
  useEffect(()=>{ const t=setTimeout(()=>setShowConfetti(false),3500); return()=>clearTimeout(t); },[]);

  return (
    <div className="absolute inset-0 bg-stone-50 flex flex-col overflow-hidden">
      {showConfetti && <ConfettiOverlay />}
      <div className="flex-1 overflow-y-auto no-scrollbar">
        {/* Success hero */}
        <div className="bg-white px-5 pt-14 pb-8 text-center">
          <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4 bounce-in">
            <Check className="text-emerald-500" size={40} strokeWidth={3} />
          </div>
          <p className="font-display font-bold text-stone-900 text-2xl">Booking Confirmed! 🎉</p>
          <p className="text-stone-500 text-sm mt-2">Your pro will arrive at the scheduled time</p>
          <div className="mt-4 bg-emerald-50 border border-emerald-200 rounded-2xl px-4 py-3">
            <p className="text-emerald-700 font-bold text-sm">Booking ID: #AGK{Math.floor(1000+Math.random()*9000)}</p>
          </div>
        </div>

        {/* Pro card */}
        <div className="bg-white mx-4 mt-4 rounded-2xl p-4 shadow-tile">
          <p className="text-xs font-bold text-stone-400 uppercase tracking-wide mb-3">Your assigned pro</p>
          <div className="flex items-center gap-3">
            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${tech.color} flex items-center justify-center text-white font-bold text-lg`}>{tech.initials}</div>
            <div className="flex-1">
              <p className="font-bold text-stone-900">{tech.name}</p>
              <p className="text-stone-500 text-xs">{tech.role} · ⭐ {tech.rating} ({tech.jobs} jobs)</p>
              <p className="text-stone-400 text-xs mt-0.5">{tech.languages}</p>
            </div>
            <div className="flex flex-col gap-2">
              <button className="w-9 h-9 bg-emerald-100 rounded-full flex items-center justify-center">
                <Phone size={14} className="text-emerald-600" />
              </button>
              <button className="w-9 h-9 bg-sky-100 rounded-full flex items-center justify-center">
                <MessageSquare size={14} className="text-sky-600" />
              </button>
            </div>
          </div>
        </div>

        {/* Booking summary */}
        <div className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-tile">
          <p className="text-xs font-bold text-stone-400 uppercase tracking-wide mb-3">Booking details</p>
          {[
            { label:"Service", value:svc.name },
            { label:"Scheduled", value:"Tomorrow, 11 AM – 1 PM" },
            { label:"Location", value:"Flat 4B, Park Avenue, Rajkot" },
          ].map(row=>(
            <div key={row.label} className="flex justify-between py-2 border-b border-stone-50 last:border-0">
              <span className="text-stone-400 text-sm">{row.label}</span>
              <span className="text-stone-800 text-sm font-semibold">{row.value}</span>
            </div>
          ))}
        </div>

        {/* Action buttons */}
        <div className="mx-4 mt-4 grid grid-cols-2 gap-3">
          <button onClick={()=>goTo("tracking")}
            className="bg-orange-500 text-white rounded-2xl py-3.5 font-bold text-sm flex items-center justify-center gap-2">
            <Navigation size={16} /> Track Live
          </button>
          <button onClick={()=>setRating(true)}
            className="bg-amber-50 text-amber-700 border border-amber-200 rounded-2xl py-3.5 font-bold text-sm flex items-center justify-center gap-2">
            <Star size={16} /> Rate Pro
          </button>
        </div>

        <div className="mx-4 mt-3">
          <button onClick={()=>goTo("home","home")}
            className="w-full bg-white border border-stone-200 text-stone-700 rounded-2xl py-3.5 font-bold text-sm">
            Back to Home
          </button>
        </div>

        <div className="h-8" />
      </div>
    </div>
  );
}

function TrackingScreen({ svc, goTo }) {
  const [status, setStatus] = useState(1); // 0=confirmed,1=assigned,2=on-way,3=arrived,4=done
  const tech = getTech(svc.id);
  const STATUSES = [
    { label:"Confirmed",   icon:"✅", desc:"Booking placed" },
    { label:"Pro assigned",icon:"👤", desc:`${tech.name} accepted` },
    { label:"On the way",  icon:"🚗", desc:"ETA ~12 min" },
    { label:"Arrived",     icon:"📍", desc:"Pro at your location" },
    { label:"Completed",   icon:"🎉", desc:"Service done!" },
  ];
  useEffect(()=>{
    if (status < 4) {
      const t = setTimeout(()=>setStatus(s=>s+1), 5000);
      return ()=>clearTimeout(t);
    }
  }, [status]);

  return (
    <div className="absolute inset-0 bg-stone-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white px-5 pt-10 pb-4 flex items-center gap-3 flex-shrink-0">
        <button onClick={()=>goTo("confirmation")} className="w-9 h-9 bg-stone-100 rounded-full flex items-center justify-center">
          <ArrowLeft size={18} className="text-stone-700" />
        </button>
        <p className="font-display font-bold text-stone-900 text-xl">Live Tracking</p>
        <div className="flex-1 flex justify-end items-center gap-1.5">
          <div className="w-2 h-2 bg-emerald-500 rounded-full pulse-dot" />
          <span className="text-xs text-emerald-600 font-bold">LIVE</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar">
        {/* Map */}
        <div className="mx-4 mt-3 h-48 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl relative overflow-hidden border border-stone-100">
          {/* Roads */}
          <div className="absolute inset-0">
            <div className="absolute top-1/2 left-0 right-0 h-2 bg-stone-200/60 -translate-y-1/2" />
            <div className="absolute top-0 bottom-0 left-1/2 w-2 bg-stone-200/60 -translate-x-1/2" />
            <div className="absolute top-1/3 left-1/4 right-1/4 h-1 bg-stone-200/40" />
            <div className="absolute top-2/3 left-1/5 right-1/3 h-1 bg-stone-200/40" />
          </div>
          {/* Destination */}
          <div className="absolute right-1/4 top-1/2 -translate-y-1/2 flex flex-col items-center">
            <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center shadow-lg">
              <HomeIcon size={14} className="text-white" />
            </div>
            <span className="text-[9px] font-bold text-orange-600 mt-1 bg-white/80 px-1.5 rounded-full">Your home</span>
          </div>
          {/* Moving pro */}
          <div className="absolute top-1/2 -translate-y-1/2 drive-pro" style={{position:"absolute",top:"calc(50% - 16px)"}}>
            <div className="relative">
              <div className="w-8 h-8 bg-gradient-to-br from-sky-500 to-sky-700 rounded-full flex items-center justify-center shadow-lg">
                <Navigation size={14} className="text-white" />
              </div>
              <div className="absolute inset-0 rounded-full bg-sky-400 opacity-40 ping" />
            </div>
          </div>
          {/* ETA card */}
          <div className="absolute bottom-3 left-3 bg-white rounded-xl px-3 py-2 shadow-md flex items-center gap-2">
            <Clock size={12} className="text-orange-500" />
            <span className="text-xs font-bold text-stone-800">ETA: ~{Math.max(0,12-status*3)} min</span>
          </div>
        </div>

        {/* Pro card */}
        <div className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-tile flex items-center gap-3">
          <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${tech.color} flex items-center justify-center text-white font-bold`}>{tech.initials}</div>
          <div className="flex-1">
            <p className="font-bold text-stone-900">{tech.name}</p>
            <p className="text-stone-500 text-xs">{tech.role} · ⭐ {tech.rating}</p>
          </div>
          <div className="flex gap-2">
            <button className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
              <Phone size={16} className="text-emerald-600" />
            </button>
            <button className="w-10 h-10 bg-sky-100 rounded-full flex items-center justify-center">
              <MessageSquare size={16} className="text-sky-600" />
            </button>
          </div>
        </div>

        {/* Status timeline */}
        <div className="bg-white mx-4 mt-3 rounded-2xl p-4 shadow-tile">
          <p className="font-bold text-stone-900 text-sm mb-4">Status</p>
          <div className="space-y-0">
            {STATUSES.map((s,i) => (
              <div key={i} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 transition-all ${i<status?"bg-emerald-100":i===status?"bg-orange-500 scale-110":"bg-stone-100"}`}>
                    {i < status ? "✓" : s.icon}
                  </div>
                  {i < STATUSES.length-1 && (
                    <div className={`w-0.5 h-6 my-0.5 rounded-full ${i<status?"bg-emerald-300":"bg-stone-100"}`} />
                  )}
                </div>
                <div className={`pb-4 ${i===STATUSES.length-1?"pb-0":""}`}>
                  <p className={`text-sm font-semibold ${i===status?"text-orange-600":i<status?"text-emerald-600":"text-stone-400"}`}>{s.label}</p>
                  <p className="text-stone-400 text-xs">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {status >= 4 && (
          <div className="mx-4 mt-3 fade-in">
            <button onClick={()=>goTo("confirmation")}
              className="w-full bg-emerald-500 text-white rounded-2xl py-4 font-bold text-sm flex items-center justify-center gap-2">
              <CheckCircle size={18} /> Service Completed! Rate Now
            </button>
          </div>
        )}

        <div className="h-8" />
      </div>
    </div>
  );
}

function BookingsScreen({ goTo, bookings }) {
  const ACTIVE = (bookings || []).filter(b => b.active);
  const PAST = (bookings || []).filter(b => !b.active);
  return (
    <div className="absolute inset-0 bg-stone-50 flex flex-col overflow-hidden">
      <div className="bg-white px-5 pt-10 pb-4 flex-shrink-0">
        <p className="font-display font-bold text-stone-900 text-2xl">My Bookings</p>
      </div>
      <div className="flex-1 overflow-y-auto no-scrollbar px-4 pt-4">
        <p className="text-xs font-bold text-stone-400 uppercase tracking-wide mb-3">Active</p>
        <div className="space-y-3 mb-5">
          {ACTIVE.map((b,i) => {
            const Icon = b.icon || Star;
            return (
            <div key={i} className="bg-white rounded-2xl p-4 shadow-tile">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 ${b.color || 'bg-stone-500'} rounded-xl flex items-center justify-center`}>
                  <Icon size={18} className="text-white" />
                </div>
                <div className="flex-1">
                  <p className="font-bold text-stone-900 text-sm">{b.svc}</p>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${b.dot} pulse-dot`} />
                    <p className="text-stone-500 text-xs">{b.status}</p>
                  </div>
                </div>
                <button onClick={()=>goTo("tracking")}
                  className="text-xs bg-orange-500 text-white px-3 py-1.5 rounded-full font-bold">
                  Track
                </button>
              </div>
            </div>
          )})}
        </div>
        <p className="text-xs font-bold text-stone-400 uppercase tracking-wide mb-3">Past bookings</p>
        <div className="space-y-3">
          {PAST.map((b,i) => {
            const Icon = b.icon || Star;
            return (
            <div key={i} className="bg-white rounded-2xl p-4 shadow-tile flex items-center gap-3">
              <div className={`w-10 h-10 ${b.color || 'bg-stone-500'} rounded-xl flex items-center justify-center`}>
                <Icon size={18} className="text-white" />
              </div>
              <div className="flex-1">
                <p className="font-bold text-stone-900 text-sm">{b.svc}</p>
                <p className="text-stone-400 text-xs">{b.date}</p>
              </div>
              <div className="flex items-center gap-1">
                {[...Array(b.rating || 5)].map((_,j)=><Star key={j} size={11} className="text-amber-400 fill-amber-400" />)}
              </div>
              <button className="text-xs text-orange-500 font-bold">Rebook</button>
            </div>
          )})}
        </div>
        <div className="h-24" />
      </div>
    </div>
  );
}

function HelpScreen() {
  const FAQS = [
    { q:"How do I reschedule?", a:"Go to My Bookings, tap your booking, then choose Reschedule." },
    { q:"Is there a cancellation charge?", a:"Free cancellation up to 2 hours before. 50% charge after that." },
    { q:"What areas does Agak cover?", a:"Currently serving all of Rajkot city and surrounding 20 km radius." },
    { q:"Are your professionals verified?", a:"Yes — all pros are background checked, ID verified and rated 4.5+." },
  ];
  const [open, setOpen] = useState(null);
  return (
    <div className="absolute inset-0 bg-stone-50 flex flex-col overflow-hidden">
      <div className="bg-white px-5 pt-10 pb-4 flex-shrink-0">
        <p className="font-display font-bold text-stone-900 text-2xl">Help & Support</p>
      </div>
      <div className="flex-1 overflow-y-auto no-scrollbar px-4 pt-4">
        <div className="grid grid-cols-2 gap-3 mb-5">
          {[{icon:"💬",label:"Live Chat"},{icon:"📞",label:"Call Us"},{icon:"📧",label:"Email"},{icon:"📝",label:"Report issue"}].map((c,i)=>(
            <button key={i} className="bg-white rounded-2xl p-4 shadow-tile flex flex-col items-center gap-2">
              <span className="text-2xl">{c.icon}</span>
              <span className="text-stone-700 text-sm font-semibold">{c.label}</span>
            </button>
          ))}
        </div>
        <p className="font-bold text-stone-900 mb-3">FAQs</p>
        <div className="space-y-2">
          {FAQS.map((f,i) => (
            <div key={i} className="bg-white rounded-2xl shadow-tile overflow-hidden">
              <button onClick={()=>setOpen(open===i?null:i)} className="w-full flex items-center justify-between px-4 py-3.5 text-left">
                <span className="font-semibold text-stone-800 text-sm">{f.q}</span>
                <ChevronDown size={16} className={`text-stone-400 transition-transform ${open===i?"rotate-180":""}`} />
              </button>
              {open===i && <div className="px-4 pb-4 text-stone-500 text-sm fade-in">{f.a}</div>}
            </div>
          ))}
        </div>
        <div className="h-24" />
      </div>
    </div>
  );
}

function OnboardingScreen({ goTo }) {
  const [step, setStep] = useState(0);
  const slides = [
    {
      title: "Verified Professionals",
      desc: "Every pro is background checked, ID verified and highly rated by your neighbours.",
      icon: Shield,
      emoji: "🛡",
      gradient: "from-emerald-400 to-teal-500",
      bg: "from-emerald-50 to-teal-50",
      accent: "text-emerald-600",
      dot: "bg-emerald-500",
    },
    {
      title: "Transparent Pricing",
      desc: "No hidden costs. See the exact price before you confirm. Fixed rates, always.",
      icon: Tag,
      emoji: "💰",
      gradient: "from-sky-400 to-blue-500",
      bg: "from-sky-50 to-blue-50",
      accent: "text-sky-600",
      dot: "bg-sky-500",
    },
    {
      title: "Book in 60 Seconds",
      desc: "Choose a service, pick a slot, and track your pro live. Done.",
      icon: ZapIcon,
      emoji: "⚡",
      gradient: "from-orange-400 to-amber-500",
      bg: "from-orange-50 to-amber-50",
      accent: "text-orange-600",
      dot: "bg-orange-500",
    },
  ];
  const s = slides[step];
  return (
    <div className={`absolute inset-0 flex flex-col overflow-hidden bg-gradient-to-b ${s.bg}`}>
      {/* Skip */}
      <div className="flex justify-end px-5 pt-12">
        <button onClick={()=>goTo("auth")} className="text-stone-400 text-xs font-bold px-3 py-1.5 rounded-full bg-white/60">
          Skip
        </button>
      </div>

      {/* Illustration */}
      <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
        <div className={`w-28 h-28 rounded-[2rem] bg-gradient-to-br ${s.gradient} flex items-center justify-center mb-8 shadow-2xl float-icon`}>
          <span className="text-5xl">{s.emoji}</span>
        </div>
        <p className="font-display font-bold text-stone-900 text-[1.6rem] leading-tight mb-3">{s.title}</p>
        <p className="text-stone-500 text-sm leading-relaxed max-w-xs">{s.desc}</p>
      </div>

      {/* Dots + CTA */}
      <div className="pb-10 px-6">
        <div className="flex justify-center gap-2 mb-8">
          {slides.map((sl, i) => (
            <button key={i} onClick={()=>setStep(i)}
              className={`h-2 rounded-full transition-all duration-300 ${step===i?`w-8 ${sl.dot}` :"w-2 bg-stone-300"}`} />
          ))}
        </div>
        {step < slides.length - 1 ? (
          <button onClick={()=>setStep(s=>s+1)}
            className={`w-full bg-gradient-to-r ${s.gradient} text-white rounded-2xl py-4 font-bold text-base shadow-lg active:scale-[0.98] transition-transform`}>
            Next →
          </button>
        ) : (
          <button onClick={()=>goTo("auth")}
            className="w-full bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-2xl py-4 font-bold text-base shadow-lg shadow-orange-500/30 active:scale-[0.98] transition-transform">
            Get Started ✨
          </button>
        )}
      </div>
    </div>
  );
}

function AuthScreen({ goTo, setUser, user }) {
  const [phone, setPhone] = useState(user?.rawPhone || "");
  const formatted = phone.replace(/(\d{5})(\d{1,5})/, "$1 $2");
  return (
    <div className="absolute inset-0 bg-white flex flex-col overflow-hidden fade-in">
      {/* Top illustration */}
      <div className="bg-gradient-to-br from-orange-50 to-amber-50 px-5 pt-12 pb-8 text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-amber-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg float-icon">
          <Phone size={28} className="text-white" />
        </div>
        <p className="font-display font-bold text-stone-900 text-2xl mb-1">What's your number?</p>
        <p className="text-stone-500 text-sm">We'll send a 4-digit OTP to verify</p>
      </div>

      <div className="px-5 pt-6 flex-1">
        {/* Phone input */}
        <div className="flex items-center gap-3 border-2 border-stone-200 focus-within:border-orange-500 rounded-2xl px-4 py-3.5 bg-stone-50 focus-within:bg-orange-50/30 glow-focus transition-all mb-3">
          <div className="flex items-center gap-2 border-r border-stone-300 pr-3 flex-shrink-0">
            <span className="text-lg">🇮🇳</span>
            <span className="text-stone-700 font-bold text-sm">+91</span>
          </div>
          <input type="tel" value={formatted} onChange={e=>setPhone(e.target.value.replace(/\D/g,"").slice(0,10))}
            className="flex-1 bg-transparent text-xl font-bold text-stone-900 outline-none placeholder-stone-300 tracking-widest"
            placeholder="98765 43210" autoFocus inputMode="numeric" />
          {phone.length === 10 && <Check size={18} className="text-emerald-500 flex-shrink-0" />}
        </div>
        <p className="text-stone-400 text-xs px-1">By continuing, you agree to our Terms & Privacy Policy</p>

        {/* Popular country hint */}
        <div className="mt-6 bg-stone-50 rounded-2xl p-4">
          <p className="text-xs font-bold text-stone-400 uppercase tracking-wide mb-2">Why phone number?</p>
          <div className="space-y-2">
            {["No passwords to remember","Instant OTP login","Secure & private"].map((t,i)=>(
              <div key={i} className="flex items-center gap-2">
                <div className="w-4 h-4 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Check size={9} className="text-emerald-600" strokeWidth={3} />
                </div>
                <span className="text-stone-600 text-xs">{t}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="px-5 pb-8">
        <button disabled={phone.length < 10}
          onClick={()=>{ setUser&&setUser(u=>({...u, rawPhone:phone, phone:"+91 "+phone.slice(0,5)+"*****"})); goTo("otp"); }}
          className="w-full bg-orange-500 text-white disabled:bg-stone-200 disabled:text-stone-400 rounded-2xl py-4 font-bold text-base active:scale-[0.98] transition-all flex items-center justify-center gap-2">
          Send OTP
          {phone.length===10 && <span className="text-orange-200 text-sm">→</span>}
        </button>
      </div>
    </div>
  );
}

function OtpScreen({ goTo, user }) {
  const [digits, setDigits] = useState(["","","",""]);
  const [success, setSuccess] = useState(false);
  const [error, setError]     = useState(false);
  const [resent, setResent]   = useState(false);
  const [timer, setTimer]     = useState(30);
  const refs = [useRef(), useRef(), useRef(), useRef()];
  const otp = digits.join("");

  // Countdown timer
  useEffect(()=>{
    if (timer <= 0) return;
    const t = setInterval(()=>setTimer(n=>n-1), 1000);
    return ()=>clearInterval(t);
  }, [timer]);

  const handleChange = (i, val) => {
    val = val.replace(/\D/g,"").slice(-1);
    const next = [...digits];
    next[i] = val;
    setDigits(next);
    if (val && i < 3) refs[i+1].current?.focus();
    // Auto-verify when all filled
    if (val && i === 3) {
      const full = next.join("");
      setTimeout(()=>verify(full), 100);
    }
  };

  const handleKeyDown = (i, e) => {
    if (e.key==="Backspace" && !digits[i] && i > 0) refs[i-1].current?.focus();
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g,"").slice(0,4);
    if (pasted.length === 4) {
      setDigits(pasted.split(""));
      refs[3].current?.focus();
      setTimeout(()=>verify(pasted), 100);
    }
    e.preventDefault();
  };

  const verify = (code) => {
    if (code === "1234") {
      setError(false);
      setSuccess(true);
      setTimeout(()=>goTo("name"), 1600);
    } else {
      setError(true);
      setDigits(["","","",""]);
      refs[0].current?.focus();
      setTimeout(()=>setError(false), 700);
    }
  };

  const resend = () => { setTimer(30); setResent(true); setTimeout(()=>setResent(false), 2000); };
  const displayPhone = user?.phone || "+91 98*** *****";

  return (
    <div className="absolute inset-0 bg-white flex flex-col overflow-hidden fade-in">
      {success && <ConfettiOverlay />}

      {/* Header */}
      <div className="px-5 pt-12 pb-6">
        <button onClick={()=>goTo("auth")} className="w-9 h-9 bg-stone-100 rounded-full flex items-center justify-center mb-6 active:scale-90 transition-transform">
          <ArrowLeft size={18} className="text-stone-700" />
        </button>
        <p className="font-display font-bold text-stone-900 text-2xl mb-1">Enter OTP</p>
        <div className="flex items-center gap-2">
          <p className="text-stone-500 text-sm">Sent to <span className="font-bold text-stone-800">{displayPhone}</span></p>
          <button onClick={()=>goTo("auth")} className="text-orange-500 text-xs font-bold">Edit</button>
        </div>
      </div>

      <div className="px-5 flex-1">
        {/* OTP boxes */}
        <div className={`flex gap-3 justify-center mb-2 relative ${error?"shake":""}`} onPaste={handlePaste}>
          {success && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bounce-in">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center shadow-lg">
                <Check className="text-emerald-500" size={36} strokeWidth={3} />
              </div>
            </div>
          )}
          {[0,1,2,3].map(i => (
            <input key={i} ref={refs[i]} type="tel" inputMode="numeric" maxLength={1}
              value={digits[i]}
              onChange={e=>handleChange(i, e.target.value)}
              onKeyDown={e=>handleKeyDown(i, e)}
              className={`w-16 h-16 border-2 rounded-2xl text-center text-2xl font-bold outline-none transition-all
                ${error?"border-red-400 bg-red-50 text-red-500 shake":
                  digits[i]?"border-orange-500 bg-orange-50 text-orange-600 pop":
                  "border-stone-200 focus:border-orange-400 focus:bg-orange-50/50 text-stone-900"}`} />
          ))}
        </div>

        {error && (
          <p className="text-center text-sm font-semibold text-red-500 mt-3 fade-in">
            ❌ Wrong OTP — hint: try <span className="font-mono font-bold">1234</span>
          </p>
        )}

        {/* Resend */}
        <div className="text-center mt-5">
          {timer > 0 ? (
            <p className="text-stone-400 text-sm">Resend in <span className="font-bold text-stone-600">{timer}s</span></p>
          ) : (
            <button onClick={resend} className="text-orange-500 text-sm font-bold active:scale-95 transition-transform">
              {resent ? "✓ OTP sent again!" : "Resend OTP"}
            </button>
          )}
        </div>

        {/* Hint box */}
        <div className="mt-6 bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
          <span className="text-lg mt-0.5">💡</span>
          <div>
            <p className="text-amber-800 text-xs font-bold">Demo mode</p>
            <p className="text-amber-700 text-xs mt-0.5">Use OTP <span className="font-mono font-bold">1234</span> to continue</p>
          </div>
        </div>
      </div>

      <div className="px-5 pb-8">
        <button disabled={otp.length < 4 || success} onClick={()=>verify(otp)}
          className={`w-full text-white disabled:bg-stone-200 disabled:text-stone-400 rounded-2xl py-4 font-bold text-base active:scale-[0.98] transition-all ${success?"bg-emerald-500":"bg-orange-500"}`}>
          {success ? "✓ Verified!" : "Verify OTP"}
        </button>
      </div>
    </div>
  );
}

function NameScreen({ goTo, setUser }) {
  const [name, setName] = useState("");
  const trimmed = name.trim();
  return (
    <div className="absolute inset-0 bg-white flex flex-col overflow-hidden fade-in">
      <div className="bg-gradient-to-br from-violet-50 to-fuchsia-50 px-5 pt-12 pb-8 text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-violet-400 to-fuchsia-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg float-icon">
          <span className="text-3xl">👋</span>
        </div>
        <p className="font-display font-bold text-stone-900 text-2xl mb-1">What's your name?</p>
        <p className="text-stone-500 text-sm">So your pro can greet you properly!</p>
      </div>

      <div className="px-5 pt-6 flex-1">
        <div className="border-2 border-stone-200 focus-within:border-orange-500 rounded-2xl px-4 py-3.5 bg-stone-50 focus-within:bg-orange-50/30 glow-focus transition-all mb-4">
          <input value={name} onChange={e=>setName(e.target.value)} autoFocus
            className="w-full bg-transparent text-xl font-bold text-stone-900 outline-none placeholder-stone-300"
            placeholder="Akash Kumar" maxLength={30} />
        </div>

        {/* Name suggestions */}
        <div className="flex gap-2 flex-wrap">
          {["Akash","Priya","Rahul","Neha","Vijay","Pooja"].map(n=>(
            <button key={n} onClick={()=>setName(n)}
              className="px-3 py-1.5 bg-stone-100 text-stone-600 rounded-xl text-sm font-semibold active:scale-95 transition-transform">
              {n}
            </button>
          ))}
        </div>
      </div>

      <div className="px-5 pb-8">
        <button disabled={trimmed.length < 2}
          onClick={()=>{ setUser&&setUser(u=>({...u, name:trimmed})); goTo("location"); }}
          className="w-full bg-orange-500 text-white disabled:bg-stone-200 disabled:text-stone-400 rounded-2xl py-4 font-bold text-base active:scale-[0.98] transition-all">
          {trimmed.length >= 2 ? `Continue as ${trimmed.split(" ")[0]} →` : "Enter your name"}
        </button>
      </div>
    </div>
  );
}

function LocationScreen({ goTo, user, setUser }) {
  const [manual, setManual] = useState(false);
  const [locInput, setLocInput] = useState("");

  const handleSetLocation = (loc) => {
    if (setUser) setUser(u => ({...u, location: loc}));
    goTo("home", "home");
  };

  return (
    <div className="absolute inset-0 bg-stone-50 flex flex-col overflow-hidden fade-in">
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <div className="w-24 h-24 bg-sky-100 rounded-full flex items-center justify-center mb-8 relative">
          <div className="absolute inset-0 rounded-full border-2 border-sky-400 radar-pulse" style={{ animationDelay: '0s' }} />
          <div className="absolute inset-0 rounded-full border-2 border-sky-400 radar-pulse" style={{ animationDelay: '1s' }} />
          <MapPin size={40} className="text-sky-500 relative z-10" />
        </div>
        <p className="font-display font-bold text-stone-900 text-2xl mb-3">Where do you need the service?</p>
        <p className="text-stone-500 text-sm leading-relaxed mb-10">We need your location to show available pros and services near you.</p>
        
        {manual ? (
          <div className="w-full flex gap-2 scale-in mb-3">
            <input value={locInput} onChange={e=>setLocInput(e.target.value)} autoFocus
              className="flex-1 border-2 border-stone-200 focus:border-orange-500 rounded-2xl px-4 py-3 outline-none text-stone-900 font-semibold"
              placeholder="e.g. Ahmedabad, Gujarat" />
            <button onClick={() => locInput && handleSetLocation(locInput)} className="bg-orange-500 text-white rounded-2xl px-5 font-bold active:scale-95 transition-transform">
              Set
            </button>
          </div>
        ) : (
          <>
            <button onClick={() => handleSetLocation("Rajkot, Gujarat")} className="w-full bg-stone-900 text-white rounded-2xl py-4 font-bold text-sm flex items-center justify-center gap-2 mb-3 active:scale-95 transition-transform">
              <Navigation size={16} /> Use current location
            </button>
            <button onClick={() => setManual(true)} className="w-full bg-white text-stone-700 border border-stone-200 rounded-2xl py-4 font-bold text-sm active:scale-95 transition-transform shadow-tile">
              Enter address manually
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function ProfileScreen({ goTo, user, bookings }) {
  const stats = [{label:"Bookings",value:(bookings||[]).length.toString()},{label:"Saved ₹",value:"1.2k"},{label:"Reviews",value:"8"}];
  return (
    <div className="absolute inset-0 bg-stone-50 flex flex-col overflow-hidden">
      <div className="bg-white px-5 pt-10 pb-4 flex-shrink-0">
        <p className="font-display font-bold text-stone-900 text-2xl">Profile</p>
      </div>
      <div className="flex-1 overflow-y-auto no-scrollbar px-4 pt-4">
        {/* Avatar */}
        <div className="bg-white rounded-2xl p-5 shadow-tile text-center mb-4">
          <div className="w-20 h-20 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-3">
            {(user?.name || "A").charAt(0).toUpperCase()}
          </div>
          <p className="font-display font-bold text-stone-900 text-xl">{user?.name || "User"}</p>
          <p className="text-stone-400 text-sm">{user?.phone || "+91 00000 00000"} · {user?.location?.split(',')[0] || "City"}</p>
          <div className="flex justify-around mt-4 pt-4 border-t border-stone-100">
            {stats.map(s=>(
              <div key={s.label} className="text-center">
                <p className="font-display font-bold text-stone-900 text-xl">{s.value}</p>
                <p className="text-stone-400 text-xs">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
        {/* Menu items */}
        {[{icon:"🏠",label:"Saved addresses"},{icon:"💳",label:"Payment methods"},{icon:"🔔",label:"Notifications"},{icon:"🛡",label:"Privacy & Security"},{icon:"🌐",label:"Language"},{icon:"⭐",label:"Rate the app"},{icon:"🚪",label:"Sign out"}].map((item,i)=>(
          <button key={i} onClick={() => item.label === "Sign out" && goTo("onboarding")} className="w-full bg-white rounded-2xl shadow-tile px-4 py-4 flex items-center gap-3 mb-2 text-left active:scale-[0.98] transition-transform">
            <span className="text-xl">{item.icon}</span>
            <span className="flex-1 font-semibold text-stone-700 text-sm">{item.label}</span>
            <ChevronRight size={16} className="text-stone-300" />
          </button>
        ))}
        <div className="h-24" />
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   ROOT APP
══════════════════════════════════════════════════════════ */
export default function AgakApp() {
  const [user, setUser]         = useState({ name: "Akash Kumar", phone: "", location: "Rajkot, Gujarat", address: "Flat 4B, Park Avenue, Rajkot" });
  const [bookings, setBookings] = useState([
    { svc: "AC Service", status: "On the way · ETA 12 min", icon: Wind, color: "bg-sky-500", id: "ac", dot: "bg-sky-400", active: true },
    { svc: "Cleaning", status: "Scheduled · Tomorrow 11 AM", icon: Sparkles, color: "bg-emerald-500", id: "cleaning", dot: "bg-emerald-400", active: true },
    { svc: "Salon", date: "May 3", rating: 5, icon: Scissors, color: "bg-rose-500", active: false },
  ]);
  const [screen, setScreen]     = useState("splash");
  const [prevScreen, setPrev]   = useState(null);
  const [activeTab, setActiveTab] = useState("home");
  const [svc, setSvc]           = useState(SERVICES[0]);
  const [payState, setPayState] = useState(null);   // null | 'processing' | 'success'
  const [quickBk,  setQuickBk]  = useState(false);
  const [rating,   setRating]   = useState(false);
  const scrollRef               = useRef(null);

  const goTo = (s, tab) => {
    setPrev(screen);
    setScreen(s);
    if (tab) setActiveTab(tab);
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  };

  const openService = (service) => { setSvc(service); goTo("service"); };

  useEffect(() => {
    if (screen === "splash") {
      const t = setTimeout(() => goTo("onboarding"), 2200);
      return () => clearTimeout(t);
    }
  }, [screen]);

  const showNav = ["home","bookings","help","profile"].includes(screen);
  const NAV = [
    { id:"home",     Icon:HomeIcon,     label:"Home" },
    { id:"bookings", Icon:ShoppingBag,  label:"Bookings" },
    { id:"help",     Icon:MessageCircle,label:"Help" },
    { id:"profile",  Icon:User,         label:"Profile" },
  ];

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: FONT_STYLES }} />
      <div className="min-h-screen bg-stone-100 font-body flex flex-col items-center justify-center p-4 sm:p-8">
        <div className="text-center mb-6 max-w-md">
          <p className="font-display text-2xl text-stone-900 font-bold tracking-tight">agak — home services</p>
          <p className="text-xs text-stone-500 mt-1 font-medium">Rajkot, Gujarat · Prototype v3</p>
        </div>

        {/* Phone frame */}
        <div className="relative">
          <div className="w-[380px] h-[800px] bg-stone-900 rounded-[3rem] p-3 shadow-phone">
            <div className="w-full h-full bg-white rounded-[2.4rem] overflow-hidden relative" ref={scrollRef}>
              {/* Notch */}
              <div className="absolute top-2 left-1/2 -translate-x-1/2 w-28 h-6 bg-stone-900 rounded-full z-50" />

              {/* Status bar */}
              {screen !== "splash" && (
                <div className="flex justify-between items-center px-7 pt-3 pb-0 text-[11px] font-bold text-stone-900 absolute top-0 left-0 right-0 z-40">
                  <span>9:41</span>
                  <span className="flex gap-1 items-center">
                    <span className="w-3 h-2 rounded-sm bg-stone-900 opacity-40" />
                    <span className="w-3 h-2 rounded-sm bg-stone-900 opacity-70" />
                    <span className="w-5 h-2 rounded-sm border border-stone-900 relative">
                      <span className="absolute inset-0.5 bg-stone-900 rounded-[1px]" />
                    </span>
                  </span>
                </div>
              )}

              {/* Screens */}
              {screen === "splash"       && <SplashScreen />}
              {screen === "onboarding"   && <OnboardingScreen goTo={goTo} />}
              {screen === "auth"         && <AuthScreen goTo={goTo} setUser={setUser} user={user} />}
              {screen === "otp"          && <OtpScreen goTo={goTo} user={user} />}
              {screen === "name"         && <NameScreen goTo={goTo} setUser={setUser} />}
              {screen === "location"     && <LocationScreen goTo={goTo} user={user} setUser={setUser} />}
              {screen === "home"         && <HomeScreen goTo={goTo} openService={openService} user={user} />}
              {screen === "service"      && <ServiceScreen svc={svc} goTo={goTo} setQuickBk={setQuickBk} />}
              {screen === "booking"      && <BookingScreen svc={svc} goTo={goTo} onPay={(total, planName, date)=>{ 
                setBookings(prev => [{ svc: svc.name, status: `Scheduled · ${date}`, icon: svc.Icon, color: svc.iconBg, id: svc.id, dot: "bg-emerald-400", active: true }, ...prev]);
                setPayState("processing"); 
              }} user={user} setUser={setUser} />}
              {screen === "confirmation" && <ConfirmScreen svc={svc} goTo={goTo} setRating={setRating} />}
              {screen === "tracking"     && <TrackingScreen svc={svc} goTo={goTo} />}
              {screen === "bookings"     && <BookingsScreen goTo={goTo} bookings={bookings} />}
              {screen === "help"         && <HelpScreen />}
              {screen === "profile"      && <ProfileScreen goTo={goTo} user={user} bookings={bookings} />}

              {/* Overlays */}
              {payState && (
                <PaymentPopup
                  total={500}
                  state={payState}
                  onPhase={setPayState}
                  onDone={()=>{ setPayState(null); goTo("confirmation"); }}
                />
              )}
              {quickBk && (
                <QuickBookSheet
                  svc={svc}
                  plan={SERVICE_PLANS[svc.id]?.[1]}
                  onClose={()=>setQuickBk(false)}
                  goTo={goTo}
                />
              )}
              {rating && (
                <RatingSheet
                  svc={svc}
                  tech={getTech(svc.id)}
                  onClose={()=>setRating(false)}
                />
              )}

              {/* Bottom nav */}
              {showNav && (
                <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-stone-100 flex z-30">
                  {NAV.map(n => (
                    <button key={n.id} onClick={()=>goTo(n.id, n.id)}
                      className={`flex-1 flex flex-col items-center py-3 gap-1 transition-colors ${activeTab===n.id?"text-orange-500":"text-stone-400"}`}>
                      <n.Icon size={20} strokeWidth={activeTab===n.id?2.5:1.8} />
                      <span className="text-[10px] font-semibold">{n.label}</span>
                      {activeTab===n.id && <div className="w-1 h-1 bg-orange-500 rounded-full" />}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Screen shortcuts */}
        <div className="mt-6 flex flex-wrap gap-2 justify-center max-w-sm">
          {[
            {label:"✨ Onboarding", s:"onboarding"},
            {label:"📱 Phone",      s:"auth"},
            {label:"🔑 OTP",        s:"otp"},
            {label:"👋 Name",       s:"name"},
            {label:"📍 Location",   s:"location"},
            {label:"🏠 Home",       s:"home",   t:"home"},
            {label:"🔧 Service",    s:"service"},
            {label:"📅 Booking",    s:"booking"},
            {label:"✅ Confirm",    s:"confirmation"},
            {label:"🗺 Track",      s:"tracking"},
            {label:"📋 Bookings",   s:"bookings", t:"bookings"},
          ].map(({label,s,t})=>(
            <button key={s} onClick={()=>goTo(s,t||null)}
              className="px-3 py-1.5 bg-white text-stone-600 text-xs font-semibold rounded-xl shadow-tile hover:bg-orange-50 hover:text-orange-600 transition-colors">
              {label}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
