/* Shared Chart.js look. Load after chart.js and before any chart is built. */
window.TT = {
    accent: '#0b5563',
    accentFill: 'rgba(11, 85, 99, 0.10)',
    ink: '#131c26',
    ink2: '#445362',
    ink3: '#5c6a77',
    grid: '#e7ecf0',
    gain: '#0f8a5f',
    loss: '#c23b3b',
    gainBar: 'rgba(15, 138, 95, 0.78)',
    lossBar: 'rgba(194, 59, 59, 0.78)',
    amberBar: 'rgba(196, 130, 28, 0.62)',
    slateBar: 'rgba(92, 106, 119, 0.42)',
    indigoBar: 'rgba(79, 99, 168, 0.55)'
};

if (window.Chart) {
    const d = Chart.defaults;
    d.font.family = "'Geist', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
    d.font.size = 12;
    d.color = TT.ink3;
    d.borderColor = TT.grid;

    d.elements.bar.borderRadius = 3;
    d.elements.line.borderWidth = 2;
    d.elements.line.tension = 0.2;
    d.elements.point.radius = 2;
    d.elements.point.hoverRadius = 4;

    d.plugins.legend.align = 'start';
    d.plugins.legend.labels.usePointStyle = true;
    d.plugins.legend.labels.boxWidth = 8;
    d.plugins.legend.labels.boxHeight = 8;
    d.plugins.legend.labels.padding = 16;

    d.plugins.tooltip.backgroundColor = TT.ink;
    d.plugins.tooltip.padding = 10;
    d.plugins.tooltip.cornerRadius = 6;
    d.plugins.tooltip.boxPadding = 4;
    d.plugins.tooltip.titleFont = { weight: '600' };

    if (d.scale && d.scale.grid) {
        d.scale.grid.color = TT.grid;
        d.scale.grid.tickColor = TT.grid;
    }
    if (d.scale && d.scale.title) {
        d.scale.title.color = TT.ink3;
        d.scale.title.font = { size: 12, weight: '500' };
    }
}
