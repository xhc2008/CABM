using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace UI
{
    public partial class main : Form
    {
        private string[] _args;
        public main(string[] args)
        {
            InitializeComponent();
            _args = args;
            if (args.Length != 0)
            {
                webView21.Source = new Uri(args[0]);
            }
        }

    }
}
